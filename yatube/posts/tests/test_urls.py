from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    urls_templates_names = {
        '/': 'posts/index.html',
        '/group/testslug/': 'posts/group_list.html',
        '/profile/auth/': 'posts/profile.html',
        '/posts/1/': 'posts/post_detail.html',
        '/posts/1/edit/': 'posts/post_create.html',
        '/create/': 'posts/post_create.html',
    }

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

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    def test_public_urls_are_accessible_for_guest_client(self):
        """Анонимному пользователю доступны общедоступные urls."""
        guest_accessible_urls = [
            '/',
            '/group/testslug/',
            '/profile/auth/',
            '/posts/1/',
        ]
        for url in guest_accessible_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_loginrequired_urls_redirect_guest_client(self):
        """Urls из login_requiered_urls перенаправляют анонима на логин."""
        login_requiered_urls = [
            '/posts/1/edit/',
            '/create/',
        ]
        for url in login_requiered_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_all_urls_are_accessible_for_auth_author(self):
        """Авторизованому пользователю - автору поста доступны все urls."""
        for url in self.urls_templates_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_urls_use_correct_templates(self):
        """Urls используют корректные шаблоны."""
        for url, template in self.urls_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_url_is_unaccessible(self):
        """Несуществующий url возвращает код 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
