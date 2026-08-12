from django.test import TestCase, override_settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты для модели User."""

    def test_create_user(self):
        """Создание обычного пользователя."""
        user = User.objects.create_user(
            login='testuser',
            email='test@example.com',
            name='Test User',
            password='testpass123',
        )
        self.assertEqual(user.login, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertEqual(user.role, User.Role.USER)
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_moderator)

    def test_create_superuser(self):
        """Создание суперпользователя."""
        user = User.objects.create_superuser(
            login='admin',
            email='admin@example.com',
            name='Admin',
            password='adminpass123',
        )
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_admin)

    def test_role_choices(self):
        """Проверка выбора ролей."""
        self.assertIn('user', [r[0] for r in User.Role.choices])
        self.assertIn('moderator', [r[0] for r in User.Role.choices])
        self.assertIn('admin', [r[0] for r in User.Role.choices])

    def test_is_moderator_property(self):
        """Свойство is_moderator."""
        user = User.objects.create_user(login='mod', email='mod@example.com', password='test123456')
        user.role = User.Role.MODERATOR
        user.save()
        self.assertTrue(user.is_moderator)

        admin = User.objects.create_superuser(login='admin', email='admin@example.com', password='test123456')
        self.assertTrue(admin.is_moderator)

        normal = User.objects.create_user(login='user', email='user@example.com', password='test123456')
        self.assertFalse(normal.is_moderator)


class AuthAPITest(APITestCase):
    """Тесты API аутентификации."""

    def setUp(self):
        self.register_data = {
            'login': 'newuser',
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        }
        self.login_data = {
            'login': 'newuser',
            'password': 'securepass123',
        }

    def test_register(self):
        """Тест регистрации."""
        response = self.client.post('/api/auth/register/', self.register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().login, 'newuser')

    def test_register_password_mismatch(self):
        """Регистрация с несовпадающими паролями."""
        data = self.register_data.copy()
        data['password_confirm'] = 'differentpass'
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        """Регистрация без обязательных полей."""
        data = {'login': 'newuser'}
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        """Тест входа."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        response = self.client.post('/api/auth/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        """Вход с неверными данными."""
        response = self.client.post('/api/auth/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Обновление токена."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        refresh_token = login_response.data['refresh']

        response = self.client.post(
            '/api/auth/refresh/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout(self):
        """Выход из системы."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(
            '/api/auth/logout/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_profile(self):
        """Получение своего профиля."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        access_token = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['login'], 'newuser')

    def test_update_profile(self):
        """Обновление профиля."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        access_token = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.patch(
            '/api/me/update/',
            {'name': 'Updated Name', 'email': 'updated@example.com'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password(self):
        """Смена пароля."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        access_token = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(
            '/api/me/password/',
            {
                'old_password': 'securepass123',
                'new_password': 'newsecurepass123',
                'new_password_confirm': 'newsecurepass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что новый пароль работает
        self.client.credentials()
        response = self.client.post(
            '/api/auth/login/',
            {'login': 'newuser', 'password': 'newsecurepass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_old(self):
        """Смена пароля с неверным старым."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        access_token = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(
            '/api/me/password/',
            {
                'old_password': 'wrongpassword',
                'new_password': 'newsecurepass123',
                'new_password_confirm': 'newsecurepass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DEBUG=True)
    def test_password_reset_request(self):
        """Запрос на восстановление пароля."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        response = self.client.post(
            '/api/auth/password/reset/request/',
            {'email': 'newuser@example.com'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('uid', response.data)
        self.assertIn('token', response.data)

    @override_settings(DEBUG=True)
    def test_password_reset_confirm(self):
        """Сброс пароля."""
        self.client.post('/api/auth/register/', self.register_data, format='json')

        # Получаем токен
        reset_response = self.client.post(
            '/api/auth/password/reset/request/',
            {'email': 'newuser@example.com'},
            format='json',
        )
        uid = reset_response.data['uid']
        token = reset_response.data['token']

        response = self.client.post(
            '/api/auth/password/reset/confirm/',
            {
                'uid': uid,
                'token': token,
                'new_password': 'newpassword123',
                'new_password_confirm': 'newpassword123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            '/api/auth/login/',
            {'login': 'newuser', 'password': 'newpassword123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_verify(self):
        """Верификация email."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        user = User.objects.first()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            '/api/auth/email/verify/',
            {'uid': uid, 'token': token},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertIsNotNone(user.email_verified_at)

    def test_email_resend(self):
        """Повторная отправка верификации."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_response = self.client.post('/api/auth/login/', self.login_data, format='json')
        access_token = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post('/api/auth/email/resend/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_profile(self):
        """Публичный профиль пользователя."""
        self.client.post('/api/auth/register/', self.register_data, format='json')
        response = self.client.get('/api/users/newuser/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['login'], 'newuser')
