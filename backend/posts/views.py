from rest_framework import status, permissions, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from .models import Post, PostLike, Tag
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    PostLikeSerializer,
    TagSerializer,
)


class PostListView(generics.ListCreateAPIView):
    """Список и создание постов."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        queryset = Post.objects.select_related(
            'author'
        ).prefetch_related('tags').all()

        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # По умолчанию показываем только опубликованные
            queryset = queryset.filter(status=Post.Status.PUBLISHED)

        # Фильтрация по тегу
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Поиск по заголовку
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        # Сортировка
        ordering = self.request.query_params.get('ordering', '-published_at')
        queryset = queryset.order_by(ordering)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer

    def perform_create(self, serializer):
        serializer.save()


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальный просмотр, обновление и удаление поста."""

    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        return Post.objects.select_related(
            'author'
        ).prefetch_related('tags', 'likers').all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def perform_destroy(self, instance):
        # Мягкое удаление
        instance.deleted_at = timezone.now()
        instance.status = Post.Status.DRAFT
        instance.save()


class PostLikeView(generics.GenericAPIView):
    """Лайк/отмена лайка поста."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Пост не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        like, created = PostLike.objects.get_or_create(
            user=request.user, post=post
        )

        if not created:
            # Удалить лайк (toggle)
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            return Response(
                {'liked': False, 'likes_count': post.likes_count},
                status=status.HTTP_200_OK,
            )

        post.likes_count += 1
        return Response(
            {'liked': True, 'likes_count': post.likes_count},
            status=status.HTTP_201_CREATED,
        )


class LikedPostsListView(generics.ListAPIView):
    """Избранные посты текущего пользователя."""

    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.select_related(
            'author'
        ).prefetch_related('tags').filter(
            likers__user=self.request.user
        ).order_by('-created_at').distinct()


class TagListView(generics.ListAPIView):
    """Список тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

