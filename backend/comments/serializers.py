from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментария."""

    author_login = serializers.CharField(source='author.login', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'body', 'author_login', 'author_name',
            'is_deleted', 'replies_count', 'replies',
            'parent', 'created_at', 'updated_at',
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_replies(self, obj):
        qs = obj.replies.filter(deleted_at__isnull=True)
        return CommentSerializer(qs, many=True).data

    def validate_parent(self, value):
        if value and value.is_deleted:
            raise serializers.ValidationError('Нельзя отвечать на удалённый комментарий')
        return value

    def create(self, validated_data):
        request = self.context['request']
        validated_data['author'] = request.user
        return super().create(validated_data)


class CommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания комментария."""

    content_type_str = serializers.CharField(source='content_type', write_only=True, required=True)

    class Meta:
        model = Comment
        fields = ['body', 'parent', 'content_type_str', 'object_id']
        read_only_fields = ['author']

    def validate_object_id(self, value):
        if not value:
            raise serializers.ValidationError('object_id обязателен')
        return value

    def validate(self, data):
        data = super().validate(data)
        ct_str = data.get('content_type')
        obj_id = data.get('object_id')
        if ct_str and obj_id:
            try:
                app_label, model = ct_str.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model)
                data['content_type'] = ct
                ct.get_object_for_this_type(pk=obj_id)
            except (ValueError, ContentType.DoesNotExist):
                raise serializers.ValidationError('Неверный content_type или объект не найден')
        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['author'] = request.user
        return super().create(validated_data)
