from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Category, Tag, Post, PostLike
from moderation.models import Moderation


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['slug', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['slug', 'created_at']


class PostListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка постов (краткий)."""

    author_login = serializers.CharField(source='author.login', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'status',
            'author_login', 'author_name', 'category_name',
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
    category = CategorySerializer(read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_liking = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'author', 'category', 'tags',
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

    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        slug_field='slug',
        required=False,
    )

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'category', 'tags', 'published_at',
        ]
        read_only_fields = ['id', 'slug']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        user = self.context['request'].user
        post = Post.objects.create(
            author=user,
            status=Post.Status.MODERATION,
            **validated_data,
        )
        post.tags.set(tags)

        # Автоматически отправляем пост на модерацию
        Moderation.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.pk,
            status=Moderation.Status.PENDING,
        )
        return post

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
