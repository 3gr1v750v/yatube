from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название группы",
        help_text="Введите название группы",
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Метка группы",
        help_text="Введите метку группы",
    )
    description = models.TextField(
        verbose_name="Описание группы", help_text="Введите описание группы"
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст сообщения",
        help_text="Введите текст для публикации поста",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
        help_text="Введите дату публикации поста",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Автор",
        help_text="Автор публикации записи",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name="Группа",
        help_text="Выберети группу для публикации",
    )
    image = models.ImageField('Картинка', upload_to='posts/', blank=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Ссылка на пост",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор",
    )
    text = models.TextField(
        verbose_name="Текст комментария",
        help_text="Введите текст для публикации комментария",
    )

    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата публикации"
    )

    class Meta:
        ordering = ["-created"]


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name="Пользователь",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="Подписан на автора",
    )
