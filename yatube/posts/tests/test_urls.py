from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

name_users = ['TestUser1', 'TestUser2']
name_slugs = ['test_group', 'bag_slug']

name_reverses = {
    'index': reverse('posts:index'),
    'group_list': reverse('posts:group_list', kwargs={'slug': name_slugs[0]}),
    'bad_group_list': reverse('posts:group_list',
                              kwargs={'slug': name_slugs[1]}),
    'profile': reverse('posts:profile', kwargs={'username': name_users[0]}),
    'login': reverse('users:login'),
    'create_post': reverse('posts:post_create'),
    'follow': reverse('posts:follow_index'),
    'about': reverse('about:author'),
    'fictin_link': '/fictin/link',
}


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username=name_users[0]
        )

        cls.another_user = User.objects.create_user(
            username=name_users[1]
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание группы',
            slug=name_slugs[0],
        )

        cls.post = Post.objects.create(
            text='Тестовые посты' * 2,
            group=cls.group,
            author=cls.author
        )

        cls.post_url = reverse(
            'posts:post_detail',
            kwargs={
                'post_id': cls.post.id
            }
        )

        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={
                'post_id': cls.post.id
            }
        )

    def setUp(self):
        self.guest_client = Client()

        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.another_client = Client()
        self.another_client.force_login(self.another_user)
        cache.clear()

    def test_group_user_urls_status_code(self):
        """Проверяем всех пользователя на общей доступности"""
        url_names = [
            [self.guest_client, name_reverses['index'], HTTPStatus.OK],
            [self.guest_client, name_reverses['group_list'], HTTPStatus.OK],
            [self.guest_client, name_reverses['profile'], HTTPStatus.OK],
            [self.guest_client, self.post_url, HTTPStatus.OK],
            [self.guest_client, name_reverses['bad_group_list'],
             HTTPStatus.NOT_FOUND],
            [self.guest_client, name_reverses['fictin_link'],
             HTTPStatus.NOT_FOUND],

            [self.another_client, self.post_edit_url,
             HTTPStatus.FOUND],
            [self.another_client, name_reverses['create_post'],
             HTTPStatus.OK],

            [self.author_client, self.post_edit_url, HTTPStatus.OK],
            [self.author_client, name_reverses['create_post'], HTTPStatus.OK],
        ]

        for client, url, http_status in url_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, http_status)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = [
            [name_reverses['index'], 'posts/index.html'],
            [name_reverses['group_list'], 'posts/group_list.html'],
            [name_reverses['profile'], 'posts/profile.html'],
            [name_reverses['follow'], 'posts/follow.html'],
            [self.post_url, 'posts/post_detail.html'],
            [self.post_edit_url, 'posts/update_post.html'],
            [name_reverses['create_post'], 'posts/create_post.html']
        ]

        for url, template in templates_url_names:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
