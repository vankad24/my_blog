"""Тесты восстановления гостевого посетителя по IP."""
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from users.testing import RedisTestCaseMixin


class GuestIdentityByIPTests(RedisTestCaseMixin, APITestCase):
    """Инкогнито получает новый токен, но того же гостевого посетителя."""

    def guest(self, ip='198.51.100.10', token=None, **extra):
        headers = dict(extra)
        if token:
            headers['HTTP_AUTHORIZATION'] = f'Guest {token}'
        return self.client.post(
            '/api/auth/guest/',
            {},
            format='json',
            REMOTE_ADDR=ip,
            **headers,
        )

    def ip_keys(self):
        return list(self.redis.scan_iter('auth:guest:ip:*'))

    def test_same_ip_gets_new_token_with_same_visitor(self):
        """После очистки localStorage токен новый, visitor_id — прежний."""
        first = self.guest()
        second = self.guest()

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertNotEqual(first.data['token'], second.data['token'])
        self.assertEqual(first.data['visitor_id'], second.data['visitor_id'])

    def test_different_ip_gets_different_visitor(self):
        """Разные IP — разные гостевые посетители."""
        first = self.guest(ip='198.51.100.10')
        second = self.guest(ip='198.51.100.11')

        self.assertNotEqual(first.data['visitor_id'], second.data['visitor_id'])

    def test_existing_token_is_returned_and_ip_mapping_refreshed(self):
        """Обычный браузер получает прежний токен, связка по IP продлевается."""
        first = self.guest()
        for key in self.ip_keys():
            self.redis.delete(key)
        self.assertEqual(self.ip_keys(), [])

        second = self.guest(token=first.data['token'])
        self.assertEqual(second.data['token'], first.data['token'])
        self.assertEqual(second.data['visitor_id'], first.data['visitor_id'])
        self.assertEqual(len(self.ip_keys()), 1)
        self.assertGreater(self.redis.ttl(self.ip_keys()[0]), 0)

    def test_invalid_token_falls_back_to_ip(self):
        """Недействительный токен не мешает восстановить посетителя по IP."""
        first = self.guest()
        second = self.guest(token='unknown-token')

        self.assertNotEqual(second.data['token'], first.data['token'])
        self.assertEqual(second.data['visitor_id'], first.data['visitor_id'])

    def test_only_ip_hash_is_stored(self):
        """В Redis попадает только HMAC-хеш IP, не сам IP."""
        self.guest(ip='198.51.100.10')

        keys = self.ip_keys()
        self.assertEqual(len(keys), 1)
        self.assertNotIn('198.51.100.10', keys[0])
        self.assertTrue(keys[0].startswith('auth:guest:ip:'))

        for key in self.redis.scan_iter('*'):
            self.assertNotIn('198.51.100.10', key)

    def test_ip_mapping_has_guest_ttl(self):
        """Связка IP -> visitor_id живёт не дольше гостевого токена."""
        self.guest()

        key = self.ip_keys()[0]
        ttl = self.redis.ttl(key)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, settings.GUEST_TOKEN_TTL)

    def test_x_forwarded_for_is_used_behind_proxy(self):
        """За nginx посетитель определяется по X-Forwarded-For."""
        first = self.guest(
            ip='127.0.0.1',
            HTTP_X_FORWARDED_FOR='203.0.113.7, 10.0.0.1',
        )
        second = self.guest(
            ip='127.0.0.1',
            HTTP_X_FORWARDED_FOR='203.0.113.7, 10.0.0.1',
        )

        self.assertEqual(first.data['visitor_id'], second.data['visitor_id'])
