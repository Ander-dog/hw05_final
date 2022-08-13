from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
        )

    def setUp(self):
        # неавторизированный пользователь
        self.guest_client = Client()
        # автор поста
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.author_user)
        # авторизированный пользователь, не автор поста
        self.common_user = User.objects.create_user(username='common')
        self.common_client = Client()
        self.common_client.force_login(self.common_user)
        cache.clear()

    def test_homepage(self):
        """Главная страница работает."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_post_pages_as_guest_client(self):
        """У анонимного пользователя корректные права доступа."""
        expected_responses = {
            f'/profile/{PostURLTests.author_user.username}/': HTTPStatus.OK,
            f'/profile/{PostURLTests.author_user.username}/follow/': (
                HTTPStatus.FOUND),
            f'/profile/{PostURLTests.author_user.username}/unfollow/': (
                HTTPStatus.FOUND),
            f'/group/{PostURLTests.group.slug}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/edit/': HTTPStatus.FOUND,
            f'/posts/{PostURLTests.post.id}/comment/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, expected_status_code in expected_responses.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_status_code)

    def test_post_pages_as_author_client(self):
        """У авторизированного пользователя корректные права доступа."""
        expected_responses = {
            f'/profile/{PostURLTests.author_user.username}/': HTTPStatus.OK,
            f'/profile/{self.common_user.username}/follow/': (
                HTTPStatus.FOUND),
            f'/profile/{self.common_user.username}/unfollow/': (
                HTTPStatus.FOUND),
            f'/group/{PostURLTests.group.slug}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/edit/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/comment/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, expected_status_code in expected_responses.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, expected_status_code)

    def test_post_edit_url_redirect_anonymous_on_login_page(self):
        """Страница по адресу /posts/<int:post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostURLTests.post.id}/edit/'
        )

    def test_post_create_url_redirect_anonymous_on_login_page(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_common_on_post_detail_page(self):
        """Страница по адресу /posts/<int:post_id>/edit/ доступна
        только для автора этого поста.
        """
        response = self.common_client.get(
            f'/posts/{PostURLTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{PostURLTests.post.id}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates = {
            '/': 'posts/index.html',
            f'/profile/{PostURLTests.author_user.username}/': (
                'posts/profile.html'),
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/index.html'
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
