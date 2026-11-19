"""Тесты серверных сессий в Redis и гостевых токенов."""
import fakeredis
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from users import redis_store

User = get_user_model()


class RedisAuthTests(APITestCase):
    """Авторизация: сессии по sid и гостевые токены."""

    def setUp(self):
        self.redis = fakeredis.FakeRedis(decode_responses=True)
        redis_store.set_redis_client(self.redis)
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            login='redisuser',
            email='redisuser@example.com',
            password=self.password,
        )

    def tearDown(self):
        redis_store.set_redis_client(None)
        self.redis.flushall()
        self.redis.close()

    def login(self):
        return self.client.post(
            '/api/auth/login/',
            {'login': self.user.login, 'password': self.password},
            format='json',
        )

    def test_login_creates_session_in_redis(self):
        """Логин создаёт серверную сессию, sid есть в access-токене."""
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sid = AccessToken(response.data['access'])['sid']
        self.assertTrue(redis_store.session_exists(sid, self.user.id))
        ttl = self.redis.ttl(f'auth:sid:{sid}')
        self.assertGreater(ttl, 0)
        self.assertLessEqual(
            ttl,
            int(self._refresh_lifetime_seconds()),
        )

    def test_token_without_sid_is_rejected(self):
        """Старые токены без sid больше не принимаются."""
        access = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(
            self.client.get('/api/me/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_rotates_and_old_refresh_is_rejected(self):
        """Ротация refresh: старый токен нельзя использовать повторно."""
        tokens = self.login().data

        first = self.client.post(
            '/api/auth/refresh/', {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertNotEqual(first.data['refresh'], tokens['refresh'])

        reused = self.client.post(
            '/api/auth/refresh/', {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

        second = self.client.post(
            '/api/auth/refresh/', {'refresh': first.data['refresh']}, format='json'
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)

    def test_logout_revokes_access_and_refresh(self):
        """Logout удаляет сессию: access и refresh перестают работать."""
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = self.client.post(
            '/api/auth/logout/', {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.client.get('/api/me/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        refresh_response = self.client.post(
            '/api/auth/refresh/', {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(
            refresh_response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_password_change_revokes_sessions(self):
        """Смена пароля отзывает все сессии пользователя."""
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = self.client.post(
            '/api/me/password/',
            {
                'old_password': self.password,
                'new_password': 'newtestpass123',
                'new_password_confirm': 'newtestpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get('/api/me/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_guest_token_created_and_reused(self):
        """Гостевой токен создаётся в Redis и переиспользуется."""
        first = self.client.post('/api/auth/guest/', {}, format='json')
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data['token_type'], 'Guest')
        self.assertTrue(first.data['token'])
        self.assertTrue(first.data['visitor_id'])

        key = f"auth:guest:{first.data['token']}"
        self.assertEqual(self.redis.get(key), first.data['visitor_id'])
        self.assertGreater(self.redis.ttl(key), 0)

        second = self.client.post(
            '/api/auth/guest/',
            {},
            format='json',
            HTTP_AUTHORIZATION=f"Guest {first.data['token']}",
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data['token'], first.data['token'])
        self.assertEqual(second.data['visitor_id'], first.data['visitor_id'])

    def test_guest_can_read_public_but_not_protected(self):
        """Гость читает публичное, но IsAuthenticated его не пропускает."""
        guest = self.client.post('/api/auth/guest/', {}, format='json').data
        self.client.credentials(HTTP_AUTHORIZATION=f"Guest {guest['token']}")

        self.assertEqual(
            self.client.get('/api/posts/').status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get('/api/me/').status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unknown_guest_token_is_ignored(self):
        """Неизвестный гостевой токен не ломает публичные запросы."""
        self.client.credentials(HTTP_AUTHORIZATION='Guest unknown-token')

        self.assertEqual(
            self.client.get('/api/posts/').status_code,
            status.HTTP_200_OK,
        )
        # Токен проигнорирован: защищённый эндпоинт просит авторизоваться
        self.assertEqual(
            self.client.get('/api/me/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def _refresh_lifetime_seconds():
        from django.conf import settings

        return settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
