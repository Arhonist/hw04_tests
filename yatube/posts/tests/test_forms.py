from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа # 2',
            slug='testslug2',
            description='Тестовое описание # 2',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_create_post(self):
        """При отправке валидной формы в create создаётся новый пост в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост # 2',
            'group': 1,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'auth'})
        )
        created_post = Post.objects.get(id=1)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(created_post.author, PostFormsTests.user)
        self.assertEqual(created_post.group, PostFormsTests.group)
        self.assertEqual(created_post.text, 'Тестовый пост # 2')
        self.assertTrue(created_post.pub_date)

    def test_post_edit_page_changes_post(self):
        """Валидная форма со страницы edit изменяет пост в БД."""
        Post.objects.create(
            author=PostFormsTests.user,
            text='Тестовый пост',
            group=PostFormsTests.group,
        )
        form_data = {
            'text': 'Текст поста # 1 был изменён',
            'group': 2,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        changed_post = Post.objects.get(id=1)
        self.assertEqual(changed_post.text, 'Текст поста # 1 был изменён')
        self.assertEqual(changed_post.group, PostFormsTests.group_2)
        self.assertEqual(changed_post.author, PostFormsTests.user)
