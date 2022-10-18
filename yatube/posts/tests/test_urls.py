from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    urls_templates_names = {
        reverse('posts:index'): 'posts/index.html',
        reverse('posts:group_list', kwargs={'slug': 'testslug'}): (
            'posts/group_list.html'
        ),
        reverse('posts:profile', kwargs={'username': 'auth'}): (
            'posts/profile.html'
        ),
        reverse('posts:post_detail', kwargs={'post_id': 1}): (
            'posts/post_detail.html'
        ),
        reverse('posts:post_edit', kwargs={'post_id': 1}): (
            'posts/post_create.html'
        ),
        reverse('posts:post_create'): 'posts/post_create.html',
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
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
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'testslug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
            reverse('posts:post_detail', kwargs={'post_id': 1}),
        ]
        for url in guest_accessible_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_loginrequired_urls_redirect_guest_client(self):
        """Urls из login_requiered_urls перенаправляют анонима на логин."""
        login_requiered_urls = [
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            reverse('posts:post_create'),
        ]
        for url in login_requiered_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(
                    response, reverse('users:login') + '?next=' + url
                )

    def test_user_who_isnt_an_author_cannot_edit_post(self):
        """Пользователь не может зайти на страницу edit чужого поста."""
        self.authorized_client.force_login(StaticURLTests.user_2)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 1})
        )

    def test_all_urls_are_accessible_for_auth_author(self):
        """Авторизованому пользователю - автору поста доступны все urls."""
        for url in self.urls_templates_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_templates(self):
        """Urls используют корректные шаблоны."""
        for url, template in self.urls_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_url_is_unaccessible(self):
        """Несуществующий url возвращает код 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unauthorized_user_cannot_leave_comments(self):
        """Аноним не может оставлять комментарии."""
        form_data = {
            'text': 'Тестовый комментарий',
            'author': StaticURLTests.user,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse('users:login')
            + '?next=' + reverse('posts:add_comment', kwargs={'post_id': 1})
        )
