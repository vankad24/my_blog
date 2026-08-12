from rest_framework import status, permissions, generics
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer


class CommentListView(generics.ListCreateAPIView):
    """Список и создание комментариев."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        queryset = Comment.objects.select_related('author').filter(
            parent__isnull=True, deleted_at__isnull=True
        )

        # Фильтрация по объекту
        content_type = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')

        if content_type and object_id:
            try:
                content_type_obj = ContentType.objects.get(
                    app_label=content_type.split('.')[0],
                    model=content_type.split('.')[1],
                )
                queryset = queryset.filter(
                    content_type=content_type_obj,
                    object_id=object_id,
                )
            except ContentType.DoesNotExist:
                queryset = queryset.none()

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальный просмотр, обновление и удаление комментария."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.select_related('author').all()

    def perform_update(self, serializer):
        # Автор может редактировать только свой комментарий
        if serializer.instance.author != self.request.user:
            return Response(
                {'error': 'Нет прав для редактирования'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer.save()

    def perform_destroy(self, serializer):
        # Мягкое удаление
        serializer.instance.deleted_at = timezone.now()
        serializer.instance.save()

