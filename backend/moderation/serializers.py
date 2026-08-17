from rest_framework import serializers
from .models import Moderation


class ModerationSerializer(serializers.ModelSerializer):
    """Сериализатор модерации."""

    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    object_id_field = serializers.IntegerField(source='object_id', read_only=True)
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = Moderation
        fields = [
            'id', 'content_type_name', 'object_id_field',
            'content_object', 'status', 'comment', 'moderator',
            'moderated_at', 'created_at',
        ]
        read_only_fields = ['moderator', 'moderated_at']

    def get_content_object(self, obj):
        # Возвращаем базовую информацию о модерируемом объекте
        content_type = obj.content_type.model
        if content_type == 'post':
            from posts.models import Post
            try:
                post = Post.objects.get(pk=obj.object_id)
                return {'type': 'post', 'title': post.title}
            except Post.DoesNotExist:
                pass
        elif content_type == 'comment':
            from comments.models import Comment
            try:
                comment = Comment.objects.get(pk=obj.object_id)
                return {'type': 'comment', 'body': comment.body[:100]}
            except Comment.DoesNotExist:
                pass
        return {'type': content_type, 'id': obj.object_id}


class ModerationActionSerializer(serializers.Serializer):
    """Сериализатор для действий модерации."""

    comment = serializers.CharField(required=False, allow_blank=True, default='')
