"""Тесты счётчика просмотров с дедупликацией в Redis."""
import fakeredis
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from posts.models import Post
from users import redis_store

User = get_user_model()


class PostViewCountTests(APITestCase):
    """Просмотр засчитывается не чаще одного раза в POST_VIEW_TTL."""

    def setUp(self):
        self.redis = fakeredis.FakeRedis(decode_responses=True)
        redis_store.set_redis_client(self.redis)
        self.password = 'testpass123'
        self.author = User.objects.create_user(
            login='viewauthor',
            email='viewauthor@example.com',
            password=self.password,
        )
        self.post = Post.objects.create(
            title='Published post',
            content='Content',
            author=self.author,
            status=Post.Status.PUBLISHED,
        )
        self.draft = Post.objects.create(
            title='Draft post',
            content='Content',
            author=self.author,
            status=Post.Status.DRAFT,
        )

    def tearDown(self):
        redis_store.set_redis_client(None)
        self.redis.flushall()
        self.redis.close()

    def post_view(self, post_id=None, headers=None):
        post_id = post_id or self.post.pk
        return self.client.post(
            f'/api/posts/{post_id}/view/', **(headers or {})
        )

    def guest_headers(self, ip):
        token = self.client.post(
            '/api/auth/guest/', {}, format='json', REMOTE_ADDR=ip
        ).data['token']
        return {'HTTP_AUTHORIZATION': f'Guest {token}'}

    def test_first_view_counted(self):
        """Первый просмотр увеличивает счётчик."""
        response = self.post_view()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['counted'])
        self.assertEqual(response.data['views'], 1)

        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)

    def test_repeat_view_within_window_not_counted(self):
        """Повторный просмотр в окне 30 минут не считается."""
        self.post_view()
        response = self.post_view()
        self.assertFalse(response.data['counted'])
        self.assertEqual(response.data['views'], 1)

        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)

    def test_different_guests_counted_separately(self):
        """Разные гостевые токены — разные посетители."""
        guest1 = self.guest_headers('198.51.100.10')
        guest2 = self.guest_headers('198.51.100.11')
        # Разные IP — разные посетители, даже без Guest-заголовка
        self.assertNotEqual(
            guest1['HTTP_AUTHORIZATION'], guest2['HTTP_AUTHORIZATION']
        )

        first = self.post_view(headers=guest1)
        second = self.post_view(headers=guest2)
        self.assertTrue(first.data['counted'])
        self.assertTrue(second.data['counted'])
        self.assertEqual(second.data['views'], 2)

        # Повтор тем же гостем не считается
        repeat = self.post_view(headers=guest1)
        self.assertFalse(repeat.data['counted'])
        self.assertEqual(repeat.data['views'], 2)

    def test_authenticated_user_counted_separately(self):
        """Авторизованный пользователь не смешивается с анонимом."""
        tokens = self.client.post(
            '/api/auth/login/',
            {'login': self.author.login, 'password': self.password},
            format='json',
        ).data
        headers = {'HTTP_AUTHORIZATION': f"Bearer {tokens['access']}"}

        first = self.post_view(headers=headers)
        second = self.post_view(headers=headers)
        self.assertTrue(first.data['counted'])
        self.assertFalse(second.data['counted'])
        self.assertEqual(second.data['views'], 1)

    def test_draft_not_counted(self):
        """Просмотры черновика не считаются."""
        response = self.post_view(post_id=self.draft.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['counted'])
        self.assertEqual(response.data['views'], 0)

        self.draft.refresh_from_db()
        self.assertEqual(self.draft.views, 0)

    def test_missing_post_returns_404(self):
        response = self.client.post('/api/posts/999999/view/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_key_has_window_ttl(self):
        """Ключ просмотра живёт POST_VIEW_TTL секунд."""
        from django.conf import settings

        self.post_view()
        keys = [
            key for key in self.redis.scan_iter('post:view:*')
        ]
        self.assertEqual(len(keys), 1)
        ttl = self.redis.ttl(keys[0])
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, settings.POST_VIEW_TTL)
