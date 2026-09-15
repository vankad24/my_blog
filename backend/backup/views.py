from pathlib import Path

from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from utils.backup_functions import stream_pg_dump, stream_tar

BACKUP_FILENAME_TEMPLATE = 'backup-postgre-{timestamp}.dump'
BACKUP_MEDIA_FILENAME_TEMPLATE = 'backup-media-{timestamp}.tar.gz'


def _access_key_denied(request):
    """True, если access_key из запроса не совпадает с settings.BACKUP_KEY."""
    access_key = request.query_params.get('access_key', '')
    return not settings.BACKUP_KEY or access_key != settings.BACKUP_KEY


def _access_denied():
    return Response(
        {'detail': 'Invalid access key'},
        status=status.HTTP_403_FORBIDDEN,
    )


def _streaming_file_response(chunks_iterator, filename):
    response = StreamingHttpResponse(
        chunks_iterator,
        content_type='application/octet-stream',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _backup_filename(template):
    timestamp = timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S')
    return template.format(timestamp=timestamp)


@api_view(['GET'])
@permission_classes([AllowAny])
def backup_db(request):
    """Дамп базы данных потоком. Доступ по ключу из query-параметра access_key."""
    if _access_key_denied(request):
        return _access_denied()

    return _streaming_file_response(
        stream_pg_dump(
            db_name=settings.DB_NAME,
            host=settings.DB_HOST,
            port=int(settings.DB_PORT),
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            format='c',
        ),
        _backup_filename(BACKUP_FILENAME_TEMPLATE),
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def backup_media(request):
    """Архив всех медиафайлов (tar.gz) потоком. Доступ по ключу access_key."""
    if _access_key_denied(request):
        return _access_denied()

    media_root = Path(settings.MEDIA_ROOT)

    # Проверяем до создания ответа: stream_tar — генератор, и его ошибка
    # пришла бы уже после отправки заголовков 200, обрезав ответ.
    if not media_root.is_dir():
        return Response(
            {'detail': f'Media directory does not exist: {media_root}'},
            status=status.HTTP_409_CONFLICT,
        )

    return _streaming_file_response(
        stream_tar(base_dir=str(media_root)),
        _backup_filename(BACKUP_MEDIA_FILENAME_TEMPLATE),
    )
