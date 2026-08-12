from rest_framework import status, permissions, generics
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from posts.models import Post
from comments.models import Comment
from .models import Moderation
from .serializers import ModerationSerializer, ModerationActionSerializer


class ModerationListView(generics.ListAPIView):
    """Список объектов на модерации."""

    serializer_class = ModerationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только модераторы и админы
        if not self.request.user.is_moderator:
            return Moderation.objects.none()

        status_filter = self.request.query_params.get('status', 'pending')
        return Moderation.objects.select_related(
            'moderator', 'content_type'
        ).filter(status=status_filter).order_by('-created_at')


class ModerationAcceptView(generics.GenericAPIView):
    """Принять объект на модерации."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModerationActionSerializer

    def post(self, request, pk):
        if not request.user.is_moderator:
            return Response(
                {'error': 'Нет прав'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            moderation = Moderation.objects.get(pk=pk)
        except Moderation.DoesNotExist:
            return Response(
                {'error': 'Не найдено'},
                status=status.HTTP_404_NOT_FOUND,
            )

        comment = request.data.get('comment', '')
        moderation.accept(
            moderator=request.user,
            comment=comment,
        )

        # Если это пост — публикуем
        content_type = moderation.content_type
        if content_type.model == 'post':
            post = Post.objects.get(pk=moderation.object_id)
            post.status = Post.Status.PUBLISHED
            post.published_at = timezone.now()
            post.save(update_fields=['status', 'published_at'])

        return Response(
            {'message': 'Объект принят', 'status': moderation.status},
            status=status.HTTP_200_OK,
        )


class ModerationDeclineView(generics.GenericAPIView):
    """Отклонить объект на модерации."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModerationActionSerializer

    def post(self, request, pk):
        if not request.user.is_moderator:
            return Response(
                {'error': 'Нет прав'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            moderation = Moderation.objects.get(pk=pk)
        except Moderation.DoesNotExist:
            return Response(
                {'error': 'Не найдено'},
                status=status.HTTP_404_NOT_FOUND,
            )

        comment = request.data.get('comment', '')
        moderation.decline(
            moderator=request.user,
            comment=comment,
        )

        return Response(
            {'message': 'Объект отклонён', 'status': moderation.status},
            status=status.HTTP_200_OK,
        )

