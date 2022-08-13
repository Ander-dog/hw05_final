from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_model_names = {
            'group': PostModelTest.group.title,
            'post': PostModelTest.post.text[:15],
        }
        for field, expected_name in expected_model_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.__getattribute__(self, field).__str__(),
                    expected_name
                )
