from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Tag, Post, PostLike
from moderation.models import Moderation


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']


class PostListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка постов (краткий)."""

    author_login = serializers.CharField(source='author.login', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'status',
            'author_login', 'author_name',
            'tags', 'views', 'likes_count',
            'published_at', 'created_at', 'is_liked',
        ]

    def get_is_liked(self, obj) -> bool:
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likers.filter(user=request.user).exists()
        return False


class PostDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра поста."""

    author = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_liking = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content',
            'author', 'tags',
            'status', 'views', 'likes_count',
            'published_at', 'created_at', 'updated_at',
            'is_liked', 'is_liking',
        ]

    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'login': obj.author.login,
            'name': obj.author.name,
        }

    def get_is_liked(self, obj) -> bool:
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likers.filter(user=request.user).exists()
        return False

    def get_is_liking(self, obj) -> bool:
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likers.filter(user=request.user).exists()
        return False


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления поста."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )
    title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content',
            'tags', 'published_at',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        # Если заголовок не передан — берём первую непустую строку контента
        if not validated_data.get('title'):
            validated_data['title'] = self.generate_title(validated_data.get('content', ''))
        user = self.context['request'].user
        # Админ и модератор — пост публикуется сразу
        is_moderator = user.role in ('moderator', 'admin')
        post = Post.objects.create(
            author=user,
            status=Post.Status.PUBLISHED if is_moderator else Post.Status.MODERATION,
            **validated_data,
        )
        post.tags.set(tags)

        # Только для обычных пользователей — создаём запись модерации
        if not is_moderator:
            Moderation.objects.create(
                content_type=ContentType.objects.get_for_model(Post),
                object_id=post.pk,
                status=Moderation.Status.PENDING,
            )
        return post

    @staticmethod
    def generate_title(content: str) -> str:
        """Первая непустая строка контента в качестве заголовка."""
        for line in content.split('\n'):
            line = line.strip()
            if line:
                return line[:500]
        return 'Без заголовка'

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        return instance


class PostLikeSerializer(serializers.ModelSerializer):
    """Сериализатор для лайков."""

    class Meta:
        model = PostLike
        fields = ['id', 'created_at']
        read_only_fields = ['created_at']