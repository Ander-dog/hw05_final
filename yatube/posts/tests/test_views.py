import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import PAGE_CAPACITY

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another_test_slug',
            description='Другое тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост без группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group_post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Пост с группой',
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Автор постов, без подписок
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)
        # Пользователь, для проверки подписок
        self.follower = User.objects.create_user(username='follower')
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostViewTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostViewTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/index.html',
        }
        for page, template in pages_templates.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context_group_post(self):
        """Пост с группой отображается на главной странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Пост с группой')
        self.assertEqual(post.author, PostViewTests.user)
        self.assertEqual(post.group, PostViewTests.group)
        self.assertEqual(
            post.image.name.split('/')[-1],
            PostViewTests.image.name
        )

    def test_index_page_show_correct_context_no_group_post(self):
        """Пост без группы отображается на главной странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][1]
        self.assertEqual(post.text, 'Пост без группы')
        self.assertEqual(post.author, PostViewTests.user)

    def test_cache_index(self):
        """Главная страница правильно работает с кэшем."""
        post = Post.objects.create(
            text='Тестовый пост для проверки кэша',
            author=PostViewTests.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        post.delete()
        response_before = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_before.content)
        cache.clear()
        response_after = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_after.content)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse(
                        'posts:group_list',
                        kwargs={'slug': PostViewTests.group.slug}
                    )))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Пост с группой')
        self.assertEqual(post.author, PostViewTests.user)
        self.assertEqual(
            post.image.name.split('/')[-1],
            PostViewTests.image.name
        )
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_in_another_group_doesnt_show_on_group_list_page(self):
        """Пост из другой группы не выводится на странице группы."""
        response = (self.authorized_client.
                    get(reverse(
                        'posts:group_list',
                        kwargs={'slug': PostViewTests.another_group.slug}
                    )))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse(
                        'posts:profile',
                        kwargs={'username': PostViewTests.user.username}
                    )))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Пост с группой')
        self.assertEqual(post.author, PostViewTests.user)
        self.assertEqual(
            post.image.name.split('/')[-1],
            PostViewTests.image.name
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse(
                        'posts:post_detail',
                        kwargs={'post_id': PostViewTests.group_post.id}
                    )))
        post = response.context['post']
        comment_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(comment_field, forms.fields.CharField)
        self.assertEqual(post.text, 'Пост с группой')
        self.assertEqual(post.id, PostViewTests.group_post.id)
        self.assertEqual(post.author, PostViewTests.user)
        self.assertEqual(
            post.image.name.split('/')[-1],
            PostViewTests.image.name
        )

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse(
                        'posts:post_edit',
                        kwargs={'post_id': PostViewTests.group_post.id}
                    )))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        self.assertEqual(response.context['is_edit'], True)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_authorized_user_can_follow_another_user(self):
        """Один авторизированный пользователь может подписаться на другого."""
        count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostViewTests.user.username}
        ))
        self.assertEqual(Follow.objects.count(), count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=PostViewTests.user
            ).exists()
        )

    def test_authorized_user_cant_follow_himself(self):
        """Авторизированный пользователь не может подписаться сам на себя."""
        count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.follower.username}
        ))
        self.assertEqual(Follow.objects.count(), count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.follower
            ).exists()
        )

    def test_authorized_user_can_unfollow(self):
        """Авторизированный пользователь может отписаться."""
        Follow.objects.create(
            user=self.follower,
            author=PostViewTests.user
        )
        count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostViewTests.user.username}
        ))
        self.assertEqual(Follow.objects.count(), count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=PostViewTests.user
            ).exists()
        )

    def test_authorized_user_cant_follow_twice(self):
        """Авторизированный пользователь не может подписаться дважды
        на другого пользователя.
        """
        count_before = Follow.objects.count()
        subscription = reverse(
            'posts:profile_follow',
            kwargs={'username': PostViewTests.user.username}
        )
        self.follower_client.get(subscription)
        self.follower_client.get(subscription)
        count_after = Follow.objects.count()
        self.assertEqual(count_before + 1, count_after)

    def test_follow_index_page_show_correct_context_for_follower(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        Follow.objects.create(
            user=self.follower,
            author=PostViewTests.user
        )
        response = (self.follower_client.get(reverse('posts:follow_index')))
        group_post = response.context['page_obj'][0]
        post = response.context['page_obj'][1]
        self.assertEqual(group_post.text, 'Пост с группой')
        self.assertEqual(group_post.author, PostViewTests.user)
        self.assertEqual(group_post.group, PostViewTests.group)
        self.assertEqual(
            group_post.image.name.split('/')[-1],
            PostViewTests.image.name
        )
        self.assertEqual(post.text, 'Пост без группы')
        self.assertEqual(post.author, PostViewTests.user)

    def test_follow_index_page_show_correct_context_without_followings(self):
        """Посты не отображаются, если пользователь не подписан."""
        response = (self.follower_client.get(reverse('posts:follow_index')))
        self.assertEqual(len(response.context['page_obj']), 0)


class PostViewPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user,
            text='Пост без группы',
        )
        for i in range(15):
            Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Тестовый пост номер {i+1}',
            )

    def setUp(self):
        # Автор постов, без подписок
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewPaginatorTests.user)
        # Пользователь, для проверки подписок
        self.follower = User.objects.create_user(username='follower')
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        cache.clear()

    def test_first_index_page_contains_ten_records(self):
        """Paginator выводит правильное количество постов
        на первую страницу главной страницы.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), PAGE_CAPACITY)

    def test_index_first_page_show_correct_context(self):
        """Paginator выводит правильные посты
        на первую страницу главной страницы.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        for i in range(10):
            with self.subTest(i=i):
                post = response.context['page_obj'][i]
                self.assertEqual(post.text, f'Тестовый пост номер {15-i}')
                self.assertEqual(post.author, PostViewPaginatorTests.user)

    def test_second_index_page_contains_six_records(self):
        """Paginator выводит правильное количество постов
        на вторую страницу главной страницы.
        """
        response = (self.authorized_client.
                    get(reverse('posts:index') + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_index_second_page_show_correct_context(self):
        """Paginator выводит правильные посты
        на вторую страницу главной страницы.
        """
        response = (self.authorized_client.
                    get(reverse('posts:index') + '?page=2'))
        for i in range(5):
            with self.subTest(i=i):
                post = response.context['page_obj'][i]
                self.assertEqual(post.text, f'Тестовый пост номер {5-i}')
                self.assertEqual(post.author, PostViewPaginatorTests.user)

    def test_first_group_list_page_contains_ten_records(self):
        """Paginator выводит правильное количество постов
        на первую страницу страницы группы.
        """
        response = (self.authorized_client.
                    get(reverse(
                        'posts:group_list',
                        kwargs={'slug': PostViewPaginatorTests.group.slug}
                    )))
        self.assertEqual(len(response.context['page_obj']), PAGE_CAPACITY)

    def test_second_group_list_page_contains_five_records(self):
        """Paginator выводит правильное количество постов
        на вторую страницу страницы группы.
        """
        response = (self.authorized_client.
                    get(reverse(
                        'posts:group_list',
                        kwargs={'slug': PostViewPaginatorTests.group.slug}
                    ) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_first_profile_page_contains_ten_records(self):
        """Paginator выводит правильное количество постов
        на первую страницу страницы профиля.
        """
        response = (self.authorized_client.
                    get(reverse(
                        'posts:profile',
                        kwargs={
                            'username': PostViewPaginatorTests.user.username
                        }
                    )))
        self.assertEqual(len(response.context['page_obj']), PAGE_CAPACITY)

    def test_second_profile_page_contains_six_records(self):
        """Paginator выводит правильное количество постов
        на вторую страницу страницы профиля.
        """
        response = (self.authorized_client.
                    get(reverse(
                        'posts:profile',
                        kwargs={
                            'username': PostViewPaginatorTests.user.username
                        }
                    ) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_first_index_follow_page_contains_ten_records(self):
        """Paginator выводит правильное количество постов
        на первую страницу ленты подписок.
        """
        Follow.objects.create(
            user=self.follower,
            author=PostViewPaginatorTests.user
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), PAGE_CAPACITY)

    def test_second_index_follow_page_contains_six_records(self):
        """Paginator выводит правильное количество постов
        на вторую страницу ленты подписок.
        """
        Follow.objects.create(
            user=self.follower,
            author=PostViewPaginatorTests.user
        )
        response = (self.follower_client.
                    get(reverse('posts:follow_index') + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 6)
