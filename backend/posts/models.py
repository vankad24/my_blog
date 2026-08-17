from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from users.models import User


class Tag(models.Model):
    """Тег для постов."""

    name = models.CharField('Название', max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'tags'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    """Пост блога."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликован'
        MODERATION = 'moderation', 'На модерации'

    title = models.CharField('Заголовок', max_length=500, db_index=True)
    content = models.TextField('Содержание')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        db_column='user_id',
        verbose_name='Автор',
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.MODERATION,
        db_index=True,
    )
    views = models.PositiveIntegerField('Просмотры', default=0)
    likes_count = models.PositiveIntegerField('Лайки', default=0)
    published_at = models.DateTimeField('Опубликован', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)
    deleted_at = models.DateTimeField('Удалён', null=True, blank=True)
    tags = models.ManyToManyField(
        Tag,
        related_name='posts',
        blank=True,
        verbose_name='Теги',
        db_table='post_tags',
    )
    # Reverse generic relations for easy querying
    comments = GenericRelation('comments.Comment')
    moderations = GenericRelation('moderation.Moderation')

    def __str__(self) -> str:
        return self.title

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED


class PostLike(models.Model):
    """Лайк поста пользователем."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='liked_posts',
        verbose_name='Пользователь',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likers',
        verbose_name='Пост',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'post_user_likes'
        ordering = ['-created_at']
        unique_together = [('user', 'post')]

    def __str__(self) -> str:
        return f"{self.user} liked {self.post}"