from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from users.models import User


class Moderation(models.Model):
    """Модерация контента (постов и комментариев)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        ACCEPTED = 'accepted', 'Принят'
        DECLINED = 'declined', 'Отклонён'

    # Polymorphic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    comment = models.TextField('Комментарий модератора', blank=True, default='')
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderations',
        verbose_name='Модератор',
    )
    moderated_at = models.DateTimeField('Модерирован', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'moderations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self) -> str:
        return f"{self.get_status_display()}: {self.content_object}"

    def accept(self, moderator: User, comment: str = '') -> None:
        self.status = self.Status.ACCEPTED
        self.moderator = moderator
        self.comment = comment
        self.moderated_at = models.functions.Now()
        self.save(update_fields=['status', 'moderator', 'comment', 'moderated_at'])

    def decline(self, moderator: User, comment: str = '') -> None:
        self.status = self.Status.DECLINED
        self.moderator = moderator
        self.comment = comment
        self.moderated_at = models.functions.Now()
        self.save(update_fields=['status', 'moderator', 'comment', 'moderated_at'])

