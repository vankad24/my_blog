from pathlib import Path
from uuid import uuid4

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


ALLOWED_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
}

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / 'media' / 'images'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@api_view(['POST'])
@permission_classes([AllowAny])
def upload_image(request):
    """Загрузка изображений для Vditor."""
    file = request.FILES.get('file')
    if not file:
        return Response(
            {'code': 1, 'data': {'errFiles': [file.name if file else ''], 'succMap': {}}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.content_type not in ALLOWED_TYPES:
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
    image_url = f'/media/images/{filename}'

    return Response({
        'code': 0,
        'data': {
            'errFiles': [],
            'succMap': {
                file.name: image_url
            },
        },
    })

