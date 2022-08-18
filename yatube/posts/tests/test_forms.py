import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()
name_users = ['TestUser1', 'TestUser2']


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=name_users[0])
        cls.user = User.objects.create_user(username=name_users[1])
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Описание группы',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.user_comm = Client()
        self.user_comm.force_login(self.user)

    def test_create_post(self):
        """Проверка создания записи авторизированным клиентом."""
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
            'text': 'Текстовые посты',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('id')
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.author, self.author)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, self.group)
        self.assertEqual(new_post.image.name, 'posts/small.gif')

    def test_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""
        post_edit = Post.objects.create(
            text='Текст для редактирования',
            author=self.author,
            group=self.group,
        )
        form_data = {
            'text': 'Текст поста для редактирование',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post_edit.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post_edit.id}))
        self.assertEqual(Post.objects.get(
            id=post_edit.id).text, form_data['text'])

    def test_guest_user_create_post(self):
        """Проверка создания записи неавторизированным клиентом."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовые гостевые посты',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse('posts:post_create')
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment(self):
        """Проверка создания коментария авторизированным клиентом."""
        comment_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текстовые посты',
            author=self.author
        )

        form_data = {
            'text': 'Текст комментрия',
            'author': self.user
        }

        response = self.user_comm.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )

        new_comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(new_comment.author, self.user)
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.post_id, post.id)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
