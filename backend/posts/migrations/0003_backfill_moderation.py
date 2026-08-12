# Data migration: создаёт записи Moderation для существующих постов
# со статусом moderation, у которых их ещё нет.

from django.db import migrations
from django.contrib.contenttypes.models import ContentType


def create_missing_moderations(apps, schema_editor):
    Post = apps.get_model('posts', 'Post')
    Moderation = apps.get_model('moderation', 'Moderation')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    post_ct = ContentType.objects.get_for_model(Post)

    existing_post_ids = set(
        Moderation.objects.filter(
            content_type=post_ct, status='pending'
        ).values_list('object_id', flat=True)
    )

    pending_posts = Post.objects.filter(status='moderation')
    for post in pending_posts:
        if post.pk in existing_post_ids:
            continue
        Moderation.objects.create(
            content_type=post_ct,
            object_id=post.pk,
            status='pending',
        )


def revert(apps, schema_editor):
    """Откат — удаляем созданные модерации (безопасно, просто удалить pending)."""
    Post = apps.get_model('posts', 'Post')
    Moderation = apps.get_model('moderation', 'Moderation')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    post_ct = ContentType.objects.get_for_model(Post)
    Moderation.objects.filter(content_type=post_ct, status='pending').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_initial'),
        ('moderation', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(create_missing_moderations, revert),
    ]
