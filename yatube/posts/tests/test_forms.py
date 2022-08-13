import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )
        cls.post_form = PostForm()
        cls.comment_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_post_form_in_post_creating(self):
        """Новый пост создаётся корректно."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='first.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Этот пост создан в процессе тестирования',
            'group': PostFormTests.group.id,
            'image': image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostFormTests.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Этот пост создан в процессе тестирования',
                author=PostFormTests.user,
                group=PostFormTests.group,
                image=f'posts/{image.name}',
            ).exists()
        )

    def test_post_form_in_post_editing(self):
        """Пост редактируется корректно."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='second.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост изменён в процессе тестирования',
            'group': PostFormTests.group.id,
            'image': image,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_data,
            follow=True,
        )
        edited_post = get_object_or_404(Post, id=PostFormTests.post.id)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(
            edited_post.text,
            'Тестовый пост изменён в процессе тестирования',
        )
        self.assertEqual(edited_post.group.id, PostFormTests.group.id)
        self.assertEqual(edited_post.image.name.split('/')[-1], image.name)

    def test_post_form_labels(self):
        """У формы PostForm корректные label."""
        fields_labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in fields_labels.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostFormTests.post_form.fields[field].label,
                    expected_value
                )

    def test_post_form_help_text(self):
        """У формы PostForm корректные help_text."""
        fields_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка, которая будет прикреплена к посту',
        }
        for field, expected_value in fields_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostFormTests.post_form.fields[field].help_text,
                    expected_value
                )

    def test_anonymous_cant_comment(self):
        """Анонимный пользователь не может оставить комментарий."""
        comment_count = PostFormTests.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий гостя'
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(PostFormTests.post.comments.count(), comment_count)

    def test_authorized_can_comment_and_will_be_redirected(self):
        """Авторизированный пользователь корректно оставляет комментарий."""
        comment_count = PostFormTests.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            PostFormTests.post.comments.count(),
            comment_count + 1
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.id}
            )
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
                author=PostFormTests.user,
                post=PostFormTests.post,
            ).exists()
        )

    def test_comment_form_labels(self):
        """У формы CommentForm корректные label."""
        text_label = PostFormTests.comment_form.fields['text'].label
        self.assertEqual(text_label, 'Текст комментария')

    def test_comment_form_help_text(self):
        """У формы CommentForm корректные help_text."""
        text_help_text = PostFormTests.comment_form.fields['text'].help_text
        self.assertEqual(text_help_text, 'Введите текст комментария')
