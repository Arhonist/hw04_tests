from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_create_post(self):
        """При отправке валидной формы в create создаётся новый пост в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост # 2',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text='Тестовый пост # 2').exists()
        )

    def test_post_edit_page_changes_post(self):
        """Валидная форма со страницы edit изменяет пост в БД."""
        form_data = {
            'text': 'Текст поста # 1 был изменён'
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(
            Post.objects.get(id=1).text, 'Текст поста # 1 был изменён'
        )
