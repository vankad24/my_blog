# MyBlog — миграция с Laravel на Vue + Django

## О проекте
Веб-блог для публикации постов с комментариями, лайками, модерацией и ролевой системой.
Изначально был написан на Laravel (PHP), сейчас переписывается на Vue 3 + Django REST Framework.

## Текущий статус
Миграция завершена на 95%. Laravel-код пока не удалён и лежит в корне проекта.

## Архитектура

### Бэкенд: Django REST Framework
- **Python 3.11**, Django 5.2, DRF 3.17
- Аутентификация: JWT (djangorestframework-simplejwt)
- Документация API: drf-spectacular (Swagger: `/api/docs/`)
- База данных: PostgreSQL (my_blog, user: postgres, pass: 242424)
- Виртуальное окружение: `backend/venv/`

#### Приложения (apps)
```
backend/
├── myblog_backend/      # Настройки Django (settings, urls, wsgi)
├── users/               # User, JWT, профили, восстановление пароля
├── posts/               # Post, Category, Tag, PostLike
├── comments/            # Comment (полиморфный GenericForeignKey)
└── moderation/          # Moderation (полиморфный GenericForeignKey)
```

#### Модели
| Модель | Поля | Примечание |
|--------|------|------------|
| User | login, email, name, role, email_verified_at | login вместо username, role (user/moderator/admin) |
| Category | name, slug | |
| Tag | name, slug | |
| Post | title, slug, content, excerpt, author, category, status, views, likes_count, published_at, deleted_at | Мягкое удаление через deleted_at. Status: draft/published/moderation |
| Comment | body, author, content_type, object_id, parent, deleted_at | Полиморфный (к постам). Reply через parent |
| Moderation | content_type, object_id, status, comment, moderator | Полиморфный (к постам и комментариям). Status: pending/accepted/declined |
| PostLike | user, post, created_at | Unique: (user, post) |

#### API эндпоинты (все под `/api/`)
- `auth/login/`, `auth/register/`, `auth/logout/`, `auth/refresh/`
- `auth/password/reset/request/`, `auth/password/reset/confirm/`
- `auth/email/verify/`, `auth/email/resend/`
- `me/`, `me/update/`, `me/password/`
- `users/<login>/` — публичный профиль
- `posts/`, `posts/<slug>/`, `posts/<slug>/like/`, `posts/liked/`
- `categories/`, `tags/`
- `comments/`, `comments/<pk>/`
- `moderation/`, `moderation/<pk>/accept/`, `moderation/<pk>/decline/`

#### Особенности
- Slug генерируется автоматически из title при сохранении поста
- Мягкое удаление: Post и Comment помечаются deleted_at, но не удаляются физически
- GenericRelation на Post: `post.comments`, `post.moderations`
- GenericRelation на Comment: `comment.moderations`
- Post создаётся со статусом `moderation`, после одобрения модератором — `published`
- DEBUG=True — токены восстановления/верификации возвращаются в ответе

### Фронтенд: Vue 3 + Vite + Pinia + Tailwind CSS
- **Node.js 24**, Vue 3.5, Vite 6, Pinia 3, Axios 1.7
- Dev-сервер: `localhost:5173` (с proxy на Django localhost:8000)
- Сборка: `npm run build` → `frontend/dist/`

#### Структура src/
```
src/
├── api/client.js        # Axios с JWT-интерцепторами (auto-refresh токена)
├── router/index.js      # 10 маршрутов, guards (requiresAuth, requiresModerator)
├── stores/
│   ├── auth.js          # Pinia: login, register, logout, profile, password reset
│   └── posts.js         # Pinia: CRUD постов, лайки, комментарии, категории, теги
├── components/
│   ├── Navbar.vue       # Ссылки: Главная, Написать, Избранное, Модерация, Профиль
│   ├── Footer.vue
│   ├── PostCard.vue     # Карточка с категорией, тегами, лайком, просмотрами
│   ├── PostList.vue     # Список с skeleton loading
│   ├── Pagination.vue   # Пагинация
│   └── CommentForm.vue  # Форма создания комментария
└── views/
    ├── HomePage.vue       # Поиск, фильтры по категории/тегу, пагинация
    ├── PostDetail.vue     # Полный пост + лайки + комментарии + replies
    ├── LoginPage.vue      # Вход
    ├── RegisterPage.vue   # Регистрация
    ├── ProfilePage.vue    # Профиль + редактирование + смена пароля
    ├── CreatePost.vue     # Создание поста (textarea для HTML)
    ├── EditPost.vue       # Редактирование поста
    ├── LikedPosts.vue     # Избранные посты
    ├── ModerationPage.vue # Панель модерации (вкладки, принять/отклонить)
    └── NotFound.vue       # 404
```

### Инфраструктура
- Docker: `docker-compose.yml` (db, backend, frontend, nginx)
- Nginx: reverse proxy (`/api/` → Django, `/` → Vue)
- Фронтенд собирается в статику и отдаётся через nginx

## Команды для разработки

```bash
# Бэкенд
cd backend
python manage.py runserver                    # Запуск на :8000
python manage.py test                         # Все тесты
python manage.py test --parallel 4            # Параллельно
python manage.py makemigrations               # Создать миграции
python manage.py migrate                      # Применить миграции
python manage.py createsuperuser              # Создать админа
python manage.py shell                        # Интерактивная консоль
python manage.py show_urls                    # Все маршруты

# Фронтенд
cd frontend
npm run dev                                   # Dev-сервер на :5173
npm run build                                 # Production сборка
npm run preview                               # Превью сборки
```

## Тесты
- **69 тестов** (все проходят на PostgreSQL и SQLite)
- Покрытие: модели, API эндпоинты, аутентификация, роли, модерация
- Запускать: `python manage.py test users posts comments moderation`

## Известные особенности
1. **Rich Text Editor** — пока не реализован, контент вводится как HTML в `<textarea>`
2. **Laravel-код** — всё ещё в корне проекта (app/, routes/, config/, resources/ и т.д.)
3. **Email** — в разработке отправка выключена, токены возвращаются в ответе (DEBUG mode)
4. **Slug** — генерируется из названия, при дубликате добавляется `-1`, `-2` и т.д.
5. **JWT** — access 60 мин, refresh 7 дней, с blacklist при logout
6. **CORS** — настроен на `localhost:5173` и `localhost:3000`