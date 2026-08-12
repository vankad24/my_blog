from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from users.models import User


class Comment(models.Model):
    """Комментарий с поддержкой полиморфизма (к постам и другим объектам)."""

    body = models.TextField('Текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    # Polymorphic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    comment_object = GenericForeignKey('content_type', 'object_id')
    # Reverse generic relation for moderation
    moderations = GenericRelation('moderation.Moderation')

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Родительский комментарий',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)
    deleted_at = models.DateTimeField('Удалён', null=True, blank=True)

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.comment_object}"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def replies_count(self) -> int:
        return self.replies.filter(deleted_at__isnull=True).count()

