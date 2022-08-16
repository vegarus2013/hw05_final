from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Описание группы',
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Проверка создания записи авторизированным клиентом."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текстовые посты',
            'group': self.group.id,
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
