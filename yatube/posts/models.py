from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='Название группы', max_length=200)
    slug = models.SlugField(verbose_name='Уникальное имя', unique=True)
    description = models.TextField(verbose_name='Описание группы')

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = ("Группы")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Введите текст поста',
        validators=[
            MinLengthValidator(
                limit_value=10,
                message=('Текст слишком короткий, минимум 10 символов')
            )
        ]
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = ("Посты")
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        help_text='Комментария, к которой будет относиться пост',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст комментарий',
    )
    created = models.DateTimeField(
        verbose_name='Создан',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Комментария"
        verbose_name_plural = ("Комментарии")
        ordering = ['-created']

    def __str__(self):
        return self.text[:10]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписался(лась) на {self.author}'
