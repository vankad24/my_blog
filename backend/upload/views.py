from pathlib import Path
from uuid import uuid4

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


ALLOWED_TYPES = {
    # Изображения
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    # Видео
    'video/mp4': '.mp4',
    'video/webm': '.webm',
    'video/ogg': '.ogg',
    'video/x-msvideo': '.avi',
    'video/x-matroska': '.mkv',
    # Аудио
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/ogg': '.ogg',
    'audio/mp4': '.m4a',
    # Документы
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.ms-powerpoint': '.pptx',
    'application/zip': '.zip',
    'application/gzip': '.gz',
    'application/x-rar-compressed': '.rar',
    'application/x-7z-compressed': '.7z',
    'application/x-tar': '.tar',
    # Текстовые файлы
    'text/plain': '.txt',
    'text/csv': '.csv',
    'text/html': '.html',
    'text/css': '.css',
    'text/javascript': '.js',
}

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / 'media'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """Загрузка файлов (изображения, видео, документы) для Vditor."""
    file = request.FILES.get('file')
    if not file:
        return Response(
            {'code': 1, 'data': {'errFiles': [''], 'succMap': {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.content_type not in ALLOWED_TYPES:
        return Response(
            {'code': 1, 'data': {'errFiles': [file.name], 'succMap': {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.size > MAX_FILE_SIZE:
        return Response(
            {'code': 1, 'data': {'errFiles': [file.name], 'succMap': {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    extension = ALLOWED_TYPES[file.content_type]
    filename = f'{uuid4()}{extension}'
    file_path = UPLOAD_DIR / filename

    with file_path.open('wb') as buffer:
        for chunk in file.chunks():
            buffer.write(chunk)

    # Относительный URL — проксируется Vite в dev и Nginx в prod
    image_url = f'/media/{filename}'

    return Response({
        'code': 0,
        'data': {
            'errFiles': [],
            'succMap': {
                file.name: image_url
            },
        },
    })

