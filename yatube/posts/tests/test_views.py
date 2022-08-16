from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

name_users = ['TestUser1', 'TestUser2']
name_slugs = ['test_group', 'bag_slug']

name_reverses = {
    'index': reverse('posts:index'),
    'create_post': reverse('posts:post_create'),
}


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=name_users[0])
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=name_slugs[0],
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовые посты',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

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

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.author_client.get(name_reverses['index'])
        self.check_post_info(response.context['page_obj'][0])

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_info(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.context['author'], self.user)
        self.check_post_info(response.context['page_obj'][0])

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.check_post_info(response.context['post'])


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

        for i in range(settings.PAGE_SIZE + 1):
            Post.objects.create(
                text=f'Тестовые посты #{i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_content(self):
        response = self.guest_client.get(name_reverses['index'])
        self.assertEqual(len(response.context['page_obj'].object_list),
                         settings.PAGE_SIZE)

    def test_second_page_content(self):
        response = self.client.get(name_reverses['index'] + '?page=2')
        self.assertEqual(len(response.context['page_obj'].object_list), 1)
