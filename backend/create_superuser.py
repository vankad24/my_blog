import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog_backend.settings')

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(login='admin').exists():
    User.objects.create_superuser(
        login='admin',
        email='admin@myblog.local',
        password='admin12345',
        name='Администратор',
        role=User.Role.ADMIN,
    )
    print('Суперпользователь admin создан!')
else:
    print('Пользователь admin уже существует')
