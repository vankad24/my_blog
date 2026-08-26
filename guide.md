# Руководство по разработке MyBlog

Проект состоит из двух частей: **backend** (Django + DRF) и **frontend** (Vue 3 + Vite).

---

## 📁 Структура проекта

```
my_blog/
├── backend/               # Django REST API
│   ├── myblog_backend/    # Настройки Django
│   ├── users/             # Приложение пользователей
│   ├── posts/             # Приложение постов
│   ├── comments/          # Приложение комментариев
│   ├── moderation/        # Приложение модерации
│   ├── manage.py          # Утилита Django
│   ├── requirements.txt   # Python-зависимости
│   ├── Dockerfile         # Docker-образ бэкенда
│   └── .env               # Настройки окружения
├── frontend/              # Vue 3 SPA
│   ├── src/               # Исходный код
│   │   ├── api/           # HTTP-клиент (Axios)
│   │   ├── router/        # Маршруты
│   │   ├── stores/        # Pinia store
│   │   ├── components/    # Общие компоненты
│   │   └── views/         # Страницы
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── dist/              # Сборка (создаётся командой build)
├── docker-compose.yml     # Docker Compose
├── nginx.conf             # Nginx reverse proxy
└── guide.md               # Этот файл
```

---

## 🚀 Быстрый старт

### 1. Активировать виртуальное окружение Python

```bash
# Windows (PowerShell)
backend\venv\Scripts\Activate.ps1

# Windows (CMD)
backend\venv\Scripts\activate.bat

# Linux / macOS
source backend/venv/bin/activate
```

Если виртуального окружения нет — создать:

```bash
# Windows
python -m venv backend\venv

# Linux / macOS
python3 -m venv backend/venv
```

### 2. Установить зависимости

```bash
# Python
pip install -r backend\requirements.txt

# Node.js (фронтенд)
cd frontend && npm install && cd ..
```

### 3. Настроить базу данных

Отредактировать `backend/.env`:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=my_blog
DB_USER=postgres
DB_PASSWORD=242424
DB_HOST=localhost
DB_PORT=5432
```

### 4. Применить миграции

```bash
cd backend
python manage.py migrate --verbosity=1
cd ..
```

### 5. Запустить серверы

**Терминал 1 — Django API:**

```bash
cd backend
python manage.py runserver
# → http://localhost:8000
```

**Терминал 2 — Vue фронтенд:**

```bash
cd frontend
npm run dev
# → http://localhost:5173
```

**Или одной командой (Linux/macOS):**

```bash
# Запустить оба сервера параллельно
cd backend && python manage.py runserver &
cd frontend && npm run dev &
```

---

## 🧪 Тестирование

### Django (бэкенд)

```bash
# Все тесты
cd backend
python manage.py test

# Тесты конкретного приложения
python manage.py test users
python manage.py test posts
python manage.py test comments
python manage.py test moderation

# Один тестовый класс
python manage.py test users.tests.AuthAPITest

# Один тест
python manage.py test users.tests.AuthAPITest.test_register

# С подробным выводом
python manage.py test --verbosity=2

# Параллельно (быстрее на PostgreSQL)
python manage.py test --parallel 4
```

### Vue (фронтенд)

```bash
# Проверить, что проект собирается
cd frontend
npm run build

# Режим preview (проверить production-сборку локально)
npm run preview
```

---

## 📦 Миграции базы данных

### Создать миграции после изменения моделей

```bash
cd backend
python manage.py makemigrations
```

### Просмотреть SQL, который будет выполнен

```bash
python manage.py sqlmigrate <app_name> <migration_number>
# Пример:
python manage.py sqlmigrate posts 0001
```

### Применить миграции

```bash
python manage.py migrate
```

### Откатить миграцию

```bash
python manage.py migrate <app_name> <предыдущий_номер>
# Пример: откатить posts до начального состояния
python manage.py migrate posts 0000
```

### Показать статус миграций

```bash
python manage.py showmigrations
```

---

## 🔧 Утилиты manage.py

```bash
# Создать суперпользователя (администратор)
python manage.py createsuperuser

# Открыть Django shell (интерактивная работа с моделями)
python manage.py shell

# Пример работы в shell:
# >>> from users.models import User
# >>> User.objects.all()
# >>> User.objects.create_user(login='test', email='test@test.com', password='12345678')

# Собрать статические файлы
python manage.py collectstatic

# Проверить проект на ошибки
python manage.py check

# Показать все URL-маршруты
python manage.py show_urls

# Очистить кеш
python manage.py clear_cache
```

---

## 🎨 Фронтенд (Vue 3 + Vite)

### Команды

```bash
cd frontend

# Запустить dev-сервер (с hot-reload)
npm run dev

# Собрать production-сборку
npm run build

# Предпросмотр production-сборки
npm run preview
```

### Структура frontend/src/

```
src/
├── main.js               # Точка входа
├── App.vue               # Корневой компонент
├── assets/
│   └── main.css          # Tailwind + глобальные стили
├── api/
│   └── client.js         # Axios с JWT-интерцепторами
├── router/
│   └── index.js          # Маршруты и guards
├── stores/
│   ├── auth.js           # Аутентификация (Pinia)
│   └── posts.js          # Посты, комментарии, теги (Pinia)
├── components/
│   ├── Navbar.vue        # Навигация
│   ├── Footer.vue        # Подвал
│   ├── PostCard.vue      # Карточка поста
│   ├── PostList.vue      # Список постов
│   ├── Pagination.vue    # Пагинация
│   └── CommentForm.vue   # Форма комментария
└── views/
    ├── HomePage.vue       # Главная (поиск, фильтры, пагинация)
    ├── PostDetail.vue     # Детальный просмотр поста
    ├── LoginPage.vue      # Вход
    ├── RegisterPage.vue   # Регистрация
    ├── ProfilePage.vue    # Профиль + редактирование
    ├── CreatePost.vue     # Создание поста
    ├── EditPost.vue       # Редактирование поста
    ├── LikedPosts.vue     # Избранные посты
    ├── ModerationPage.vue # Панель модерации
    └── NotFound.vue       # 404
```

### Vite proxy

В разработке Vite проксирует запросы к `/api/*` на Django:

```
frontend (localhost:5173) → proxy → backend (localhost:8000)
```

Настройка в `frontend/vite.config.js`:

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

---

## 🐳 Docker

### Запуск всего проекта (dev-режим)

```bash
# Только БД + бэкенд + фронтенд
docker-compose up --build
```

### Запуск в production-режиме (с Nginx)

```bash
docker-compose --profile prod up --build
```

### Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| `db` | 5432 | PostgreSQL 16 |
| `backend` | 8000 | Django + Gunicorn |
| `frontend` | 80 | Vue (Nginx, сборка) |
| `nginx` | 80 | Reverse proxy (prod) |

---

## 🗄️ БД: переключение между PostgreSQL и SQLite

### PostgreSQL (для разработки)

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=my_blog
DB_USER=postgres
DB_PASSWORD=242424
DB_HOST=localhost
DB_PORT=5432
```

### SQLite (для быстрых тестов без PostgreSQL)

```env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

---

## 📚 API документация

После запуска Django-сервера:

- **Swagger UI:** http://localhost:8000/api/docs/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

---

## 🧪 Полезные скрипты

### Создать тестовые данные вручную

```bash
cd backend
python manage.py shell
```

```python
from users.models import User
from posts.models import Post, Category, Tag

# Создать пользователя
user = User.objects.create_user(
    login='demo',
    email='demo@example.com',
    name='Демо-пользователь',
    password='demo1234'
)

# Создать категорию
cat = Category.objects.create(name='Технологии')

# Создать тег
tag = Tag.objects.create(name='python')

# Создать пост
post = Post.objects.create(
    title='Привет, мир!',
    content='<h1>Мой первый пост</h1><p>Это содержимое поста.</p>',
    excerpt='Краткое описание',
    author=user,
    category=cat,
    status=Post.Status.PUBLISHED,
)
post.tags.add(tag)
```

### Создать суперпользователя (администратор)

```bash
cd backend
python manage.py createsuperuser
```

---

## ⚠️ Частые проблемы и решения

### `ModuleNotFoundError: No module named 'django'`

```bash
# Активируйте виртуальное окружение
backend\venv\Scripts\activate.bat
# Затем установите зависимости
pip install -r backend\requirements.txt
```

### `psycopg2.OperationalError: connection to server at "localhost"`

Убедитесь, что PostgreSQL запущен. Проверьте настройки в `backend/.env`.

### `relation "users" does not exist`

```bash
cd backend
python manage.py migrate
```

### Фронтенд не видит API (ошибки CORS или 404)

Убедитесь, что Django запущен на порту 8000. Vite проксирует `/api/*` на `localhost:8000`.

### `npm run build` — ошибки импорта

Проверьте, что все импорты используют корректные пути с `@/` (алиас на `src/`).

---

## 📋 Чек-лист перед коммитом

- [ ] `python manage.py check` — нет ошибок Django
- [ ] `python manage.py test` — все тесты проходят
- [ ] `npm run build` — фронтенд собирается без ошибок
- [ ] `python manage.py makemigrations && python manage.py migrate` — миграции в порядке
- [ ] `.env` не содержит секретных данных для продакшена