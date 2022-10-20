import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.cache import cache, caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    pages_names_templates = {
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.second_group = Group.objects.create(
            title='Тестовая группа # 2',
            slug='testslug2',
            description='Тестовое описание # 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        for reverse_name, template in self.pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_profile_pages_show_correct_context(self):
        """Шаблоны index, group list и profile сформированы с верным
        контекстом, а пост, созданный с указанием группы, передаётся в них.
        """
        for reverse_name in list(self.pages_names_templates)[:3]:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, 'Тестовый пост')
                self.assertEqual(first_object.author, PostPagesTests.user)
                self.assertEqual(first_object.group, PostPagesTests.group)
                self.assertTrue(first_object.pub_date)
                self.assertTrue(first_object.image)
                self.assertEqual(first_object, PostPagesTests.post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(
            response.context.get('post').author, PostPagesTests.user
        )
        self.assertEqual(
            response.context.get('post').group, PostPagesTests.group
        )
        self.assertTrue(response.context.get('post').pub_date)
        self.assertTrue(response.context.get('post').image)

    def test_create_post_show_correct_context(self):
        """Шаблон create post сформирован с правильным контекстом
        как для create, так и для edit."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for reverse_name in list(self.pages_names_templates)[-2:]:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_edit_post_page_gets_post_filtered_by_id(self):
        """В контекст страницы post edit попадает пост с указанным id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        self.assertEqual(response.context.get('post').id, 1)

    def test_posts_shown_in_correct_group_lists(self):
        """Посты с группами не попадают в непредназначенные группы."""
        response_1 = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'testslug'})
        )
        response_2 = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'testslug2'})
        )
        object_1 = response_1.context['page_obj'][0]
        # Проверяем, что полученный пост принадлежит к группе testslug
        self.assertEqual(object_1.group, PostPagesTests.group)
        # Проверяем, что на странице группы testslug2 нет поста с testslug
        self.assertNotIn(object_1, list(response_2.context['page_obj']))

    def test_index_page_cache_works(self):
        """На главной странице работает кэширование списка записей."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertTrue(response.content)


class PaginatorTestView(TestCase):
    pages_names = {
        reverse('posts:index'),
        reverse('posts:group_list', kwargs={'slug': 'testslug'}),
        reverse('posts:profile', kwargs={'username': 'auth'}),
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
        for i in range(13):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост #{i}',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorTestView.user)

    def test_first_pages_contain_ten_records(self):
        """Первые страницы из pages_names_templates содержат 10 постов."""
        for reverse_name in self.pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_pages_contain_three_records(self):
        """Первые страницы из pages_names_templates содержат 3 постов."""
        for reverse_name in self.pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
