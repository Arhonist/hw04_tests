from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_post_name = post.text[:15]
        self.assertEqual(expected_post_name, str(post))

        group = PostModelTest.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))

    def test_post_model_has_correct_verbose_and_help_fields(self):
        """Проверяем наличие у Post.text нужных verbose_name и help_text."""
        post = PostModelTest.post
        text_attributes = {
            'verbose_name': 'Текст поста',
            'help_text': 'Текст нового поста',
        }
        for value, expected in text_attributes.items():
            with self.subTest(value=value):
                self.assertEqual(
                    getattr(post._meta.get_field('text'), value), expected)
