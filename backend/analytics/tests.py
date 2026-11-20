"""Тесты общего счётчика посещений сайта."""
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from analytics.models import SiteVisitCounter
from users.testing import RedisTestCaseMixin

User = get_user_model()

PASSWORD = 'testpass123'


class SiteVisitCounterTests(RedisTestCaseMixin, APITestCase):
    """Посещение засчитывается не чаще одного раза в SITE_VISIT_TTL."""

    def visit(self, headers=None):
        return self.client.post('/api/visits/', {}, format='json', **(headers or {}))

    def guest_headers(self):
        token = self.client.post(
            '/api/auth/guest/', {}, format='json'
        ).data['token']
        return {'HTTP_AUTHORIZATION': f'Guest {token}'}

    def test_first_visit_counted(self):
        """Первый заход увеличивает общий счётчик."""
        response = self.visit()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['counted'])
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(SiteVisitCounter.get_solo().total, 1)

    def test_repeat_visit_within_window_not_counted(self):
        """Повторный заход в течение 30 минут не считается."""
        self.visit()
        response = self.visit()
        self.assertFalse(response.data['counted'])
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(SiteVisitCounter.get_solo().total, 1)

    def test_different_guests_counted_separately(self):
        """Разные гостевые токены — разные посетители."""
        guest1 = self.guest_headers()
        guest2 = self.guest_headers()

        first = self.visit(headers=guest1)
        second = self.visit(headers=guest2)
        self.assertTrue(first.data['counted'])
        self.assertTrue(second.data['counted'])
        self.assertEqual(second.data['total'], 2)

        repeat = self.visit(headers=guest1)
        self.assertFalse(repeat.data['counted'])
        self.assertEqual(repeat.data['total'], 2)

    def test_authenticated_user_counted_separately(self):
        """Авторизованный пользователь не смешивается с гостем."""
        guest = self.guest_headers()
        self.visit(headers=guest)

        user = User.objects.create_user(
            login='visitor',
            email='visitor@example.com',
            password=PASSWORD,
        )
        tokens = self.client.post(
            '/api/auth/login/',
            {'login': user.login, 'password': PASSWORD},
            format='json',
        ).data
        headers = {'HTTP_AUTHORIZATION': f"Bearer {tokens['access']}"}

        first = self.visit(headers=headers)
        second = self.visit(headers=headers)
        self.assertTrue(first.data['counted'])
        self.assertFalse(second.data['counted'])
        self.assertEqual(second.data['total'], 2)

    def test_get_returns_total_without_increment(self):
        """GET отдаёт значение счётчика и не засчитывает посещение."""
        SiteVisitCounter.objects.create(total=42)

        response = self.client.get('/api/visits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 42)

        self.assertEqual(SiteVisitCounter.get_solo().total, 42)

    def test_total_survives_redis_reset(self):
        """Общий счётчик хранится в БД, а не только в Redis."""
        self.visit()
        self.redis.flushall()

        response = self.visit()
        self.assertTrue(response.data['counted'])
        self.assertEqual(response.data['total'], 2)

    def test_visit_key_has_window_ttl(self):
        """Ключ посещения живёт SITE_VISIT_TTL секунд."""
        self.visit()
        keys = list(self.redis.scan_iter('site:visit:*'))
        self.assertEqual(len(keys), 1)
        ttl = self.redis.ttl(keys[0])
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, settings.SITE_VISIT_TTL)
