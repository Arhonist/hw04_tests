import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_create_post(self):
        """При отправке валидной формы в create создаётся новый пост в БД."""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый пост # 2',
            'group': 1,
            'image': uploaded,
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
        self.assertTrue(created_post.image)

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

    def test_create_comment(self):
        """Валидная форма создаёт комментарий к посту."""
        Post.objects.create(
            author=PostFormsTests.user,
            text='Тестовый пост',
        )
        form_data = {
            'text': 'Тестовый комментарий',
            'author': PostFormsTests.user,
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(
            response.context.get('comments')[0].text,
            'Тестовый комментарий',
        )
        Post.objects.get(id=1).delete()
