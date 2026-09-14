from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from utils.backup_functions import stream_pg_dump

BACKUP_FILENAME_TEMPLATE = 'backup-postgre-{timestamp}.dump'


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

    filename = BACKUP_FILENAME_TEMPLATE.format(
        timestamp=timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S'),
    )

    response = StreamingHttpResponse(
        stream_pg_dump(
            db_name=settings.DB_NAME,
            host=settings.DB_HOST,
            port=int(settings.DB_PORT),
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            format='c',
        ),
        content_type='application/octet-stream',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
