import urllib.request
import json

base_url = 'http://localhost:8001/api'

# Тест 1: Проверка доступности
try:
    r = urllib.request.urlopen(f'{base_url}/docs/')
    print(f'✅ Swagger docs: {r.status}')
except Exception as e:
    print(f'❌ Swagger docs: {e}')

# Тест 2: Регистрация
try:
    data = json.dumps({
        'login': 'testuser',
        'email': 'test@example.com',
        'name': 'Test User',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/auth/register/',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    r = urllib.request.urlopen(req)
    result = json.loads(r.read())
    print(f'✅ Регистрация: {result}')
except Exception as e:
    print(f'❌ Регистрация: {e}')

# Тест 3: Логин
try:
    data = json.dumps({
        'login': 'testuser',
        'password': 'testpass123'
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/auth/login/',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    r = urllib.request.urlopen(req)
    result = json.loads(r.read())
    token = result.get('access', '')
    print(f'✅ Логин: OK (token: {token[:20]}...)')

    # Тест 4: Получить свой профиль
    req2 = urllib.request.Request(
        f'{base_url}/me/',
        headers={'Authorization': f'Bearer {token}'}
    )
    r2 = urllib.request.urlopen(req2)
    profile = json.loads(r2.read())
    print(f'✅ Профиль: {profile}')

    # Тест 5: Категории (публичный эндпоинт)
    r3 = urllib.request.urlopen(f'{base_url}/categories/')
    cats = json.loads(r3.read())
    print(f'✅ Категории: {cats}')

    # Тест 6: Посты (публичный эндпоинт)
    r4 = urllib.request.urlopen(f'{base_url}/posts/')
    posts = json.loads(r4.read())
    print(f'✅ Посты: {posts}')

except Exception as e:
    print(f'❌ Ошибка: {e}')
