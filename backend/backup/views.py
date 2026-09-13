from pathlib import Path

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

BACKUP_STUB_FILENAME = 'test-backup'


@api_view(['GET'])
@permission_classes([AllowAny])
def backup(request):
    """Запуск бэкапа. Доступ по ключу из query-параметра access_key."""
    access_key = request.query_params.get('access_key', '')
    expected_key = settings.BACKUP_KEY

    if not expected_key or access_key != expected_key:
        return Response(
            {'detail': 'Invalid access key'},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Заглушка вместо реального бэкапа
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / BACKUP_STUB_FILENAME).touch()

    return Response({'detail': 'Backup created'}, status=status.HTTP_200_OK)
