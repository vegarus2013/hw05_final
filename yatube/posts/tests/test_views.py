import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

name_users = ['TestUser1', 'TestUser2']
name_slugs = ['test_group', 'bag_slug']

name_reverses = {
    'index': reverse('posts:index'),
    'group': reverse('posts:group_list', kwargs={'slug': name_slugs[0]}),
    'profile': reverse('posts:profile', kwargs={'username': name_users[0]}),
    'create_post': reverse('posts:post_create'),
    'follow': reverse('posts:follow_index')
}


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=name_users[0])
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=name_slugs[0],
            description='Описание группы',
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='Тестовые посты',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)
        cache.clear()

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_forms_show_correct(self):
        """Проверка коректности формы."""
        context = {
            name_reverses['create_post'],
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        }
        for reverse_page in context:
            with self.subTest(reverse_page=reverse_page):
                response = self.author_client.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField
                )
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField
                )
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField
                )

    def test_page_show_correct_context(self):
        """Каждые шаблоны сформированы с правильным контекстом."""
        response_list = [
            [name_reverses['index'], '', ''],
            [name_reverses['group'], 'group', self.group],
            [name_reverses['profile'], 'author', self.user]
        ]

        for url, _get, _val in response_list:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.check_post_info(response.context['page_obj'][0])
                if _get and _val:
                    self.assertEqual(response.context[_get], _val)

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.check_post_info(response.context['post'])

    def test_cache_index_page(self):
        """Проверка работы кеша"""
        post = Post.objects.create(
            text='Пост под кеш',
            author=self.user
        )
        page_add = self.author_client.get(
            reverse('posts:index')).content
        post.delete()
        page_delete = self.author_client.get(
            reverse('posts:index')).content
        self.assertEqual(page_add, page_delete)
        cache.clear()
        page_cache_clear = self.author_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(page_add, page_cache_clear)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username=name_users[0],
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=name_slugs[0],
            description='Описание группы',
        )

        Post.objects.bulk_create(
            Post(
                text=f'Тестовые посты #{i}',
                author=cls.user,
                group=cls.group
            )
            for i in range(settings.PAGE_SIZE + 1)
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_page_content(self):
        page_num = 1
        pages = [
            [name_reverses['index'], settings.PAGE_SIZE],
            [f"{name_reverses['index']}?page=2", page_num],
            [name_reverses['group'], settings.PAGE_SIZE],
            [f"{name_reverses['group']}?page=2", page_num],
            [name_reverses['profile'], settings.PAGE_SIZE],
            [f"{name_reverses['profile']}?page=2", page_num]
        ]
        for url, page in pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj'].object_list), page)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username=name_users[0],
        )
        cls.user = User.objects.create_user(
            username=name_users[1],
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.user_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.author.id)
        self.assertEqual(follow.user_id, self.user.id)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        count_follow = Follow.objects.count()
        is_follow = Follow.objects.filter(
            user=self.user,
            author=self.author
        ).exists()

        if is_follow:
            self.user_client.post(
                reverse('posts:profile_unfollow',
                        kwargs={'username': self.author})
            )
            self.assertEqual(Follow.objects.count(), count_follow - 1)

        response = self.user_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/profile/{name_users[1]}/')

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(
            text="Подпишись на меня",
            author=self.author,
        )
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.user_client.get(name_reverses['follow'])
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            text='Подпишись на меня',
            author=self.author
        )
        response = self.user_client.get(name_reverses['follow'])
        self.assertNotIn(post, response.context['page_obj'].object_list)
