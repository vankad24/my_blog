"""Тесты регистрации с подтверждением и ограничения попыток входа/регистрации."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from users import redis_store
from users.testing import RedisTestCaseMixin

User = get_user_model()

PASSWORD = 'testpass123'
PENDING_MESSAGE = 'Ожидайте подтверждения регистрации'
RATE_LIMIT_MESSAGE = 'Слишком много попыток, попробуйте позже'


class RegistrationApprovalTests(RedisTestCaseMixin, APITestCase):
    """Новый пользователь ждёт одобрения модератора."""

    def register(self, login='newuser', email='newuser@example.com'):
        return self.client.post(
            '/api/auth/register/',
            {
                'login': login,
                'email': email,
                'name': 'New User',
                'password': PASSWORD,
                'password_confirm': PASSWORD,
            },
            format='json',
        )

    def login(self, login='newuser', password=PASSWORD, **extra):
        return self.client.post(
            '/api/auth/login/',
            {'login': login, 'password': password},
            format='json',
            **extra,
        )

    def moderator_headers(self):
        moderator = User.objects.create_superuser(
            login='moder',
            email='moder@example.com',
            password=PASSWORD,
        )
        response = self.login(login=moderator.login)
        return {'HTTP_AUTHORIZATION': f"Bearer {response.data['access']}"}

    def test_registration_creates_pending_user(self):
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], PENDING_MESSAGE)

        user = User.objects.get(login='newuser')
        self.assertEqual(
            user.registration_status, User.RegistrationStatus.PENDING
        )

    def test_pending_user_cannot_login(self):
        self.register()

        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], PENDING_MESSAGE)

    def test_pending_login_does_not_create_session(self):
        self.register()
        self.login()

        self.assertEqual(list(self.redis.scan_iter('auth:sid:*')), [])

    def test_moderator_sees_pending_registrations(self):
        self.register()
        headers = self.moderator_headers()

        response = self.client.get('/api/registrations/', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['login'], 'newuser')
        self.assertEqual(results[0]['registration_status'], 'pending')

    def test_accept_allows_login(self):
        self.register()
        user = User.objects.get(login='newuser')
        headers = self.moderator_headers()

        response = self.client.post(
            f'/api/registrations/{user.pk}/accept/', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(
            user.registration_status, User.RegistrationStatus.APPROVED
        )

        login = self.login()
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('access', login.data)

    def test_decline_blocks_login(self):
        self.register()
        user = User.objects.get(login='newuser')
        headers = self.moderator_headers()

        response = self.client.post(
            f'/api/registrations/{user.pk}/decline/', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(
            user.registration_status, User.RegistrationStatus.REJECTED
        )

        login = self.login()
        self.assertEqual(login.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(login.data['detail'], 'Регистрация отклонена')

    def test_decline_revokes_existing_sessions(self):
        user = User.objects.create_user(
            login='activeuser',
            email='activeuser@example.com',
            password=PASSWORD,
        )
        tokens = self.login(login=user.login).data
        headers = self.moderator_headers()

        response = self.client.post(
            f'/api/registrations/{user.pk}/decline/', **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )
        self.assertEqual(
            self.client.get('/api/me/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_regular_user_cannot_manage_registrations(self):
        User.objects.create_user(
            login='plainuser',
            email='plainuser@example.com',
            password=PASSWORD,
        )
        pending = User.objects.create_user(
            login='pendinguser',
            email='pendinguser@example.com',
            password=PASSWORD,
            registration_status=User.RegistrationStatus.PENDING,
        )
        tokens = self.login(login='plainuser').data
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )

        listing = self.client.get('/api/registrations/')
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(
            listing.data.get('results', listing.data), []
        )

        accept = self.client.post(
            f'/api/registrations/{pending.pk}/accept/'
        )
        self.assertEqual(accept.status_code, status.HTTP_403_FORBIDDEN)


class AuthRateLimitTests(RedisTestCaseMixin, APITestCase):
    """5 попыток входа/регистрации за 5 минут по IP и токену."""

    def create_user(self, login='ratelimit'):
        return User.objects.create_user(
            login=login,
            email=f'{login}@example.com',
            password=PASSWORD,
        )

    def login(self, login='ratelimit', password='wrongpass', **extra):
        return self.client.post(
            '/api/auth/login/',
            {'login': login, 'password': password},
            format='json',
            **extra,
        )

    def test_login_rate_limited_by_ip(self):
        self.create_user()

        for _ in range(5):
            response = self.login()
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )

        blocked = self.login()
        self.assertEqual(
            blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.assertEqual(blocked.data['detail'], RATE_LIMIT_MESSAGE)

    def test_login_rate_limited_by_guest_token(self):
        self.create_user()
        token, _ = redis_store.create_guest_session()

        # Разные IP, но один и тот же гостевой токен
        for index in range(5):
            response = self.login(
                HTTP_AUTHORIZATION=f'Guest {token}',
                REMOTE_ADDR=f'10.0.0.{index + 1}',
            )
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )

        blocked = self.login(
            HTTP_AUTHORIZATION=f'Guest {token}',
            REMOTE_ADDR='10.0.0.200',
        )
        self.assertEqual(
            blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.assertEqual(blocked.data['detail'], RATE_LIMIT_MESSAGE)

    def test_register_rate_limited(self):
        payload = {
            'login': 'spamuser',
            'email': 'spamuser@example.com',
            'name': 'Spam',
            'password': PASSWORD,
            'password_confirm': 'different-password',
        }

        for _ in range(5):
            response = self.client.post(
                '/api/auth/register/', payload, format='json'
            )
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )

        blocked = self.client.post(
            '/api/auth/register/', payload, format='json'
        )
        self.assertEqual(
            blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.assertEqual(blocked.data['detail'], RATE_LIMIT_MESSAGE)

    def test_successful_login_resets_counter(self):
        self.create_user()

        for _ in range(4):
            self.login()

        success = self.login(password=PASSWORD)
        self.assertEqual(success.status_code, status.HTTP_200_OK)

        # После успешного входа счётчик сброшен
        for _ in range(4):
            response = self.login()
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )
