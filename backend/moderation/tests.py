from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Moderation
from posts.models import Post
from comments.models import Comment
from users.models import User


class ModerationModelTest(TestCase):
    """Тесты модели Moderation."""

    def setUp(self):
        self.moderator = User.objects.create_superuser(
            login='moderator', email='mod@example.com', password='testpass123'
        )
        self.author = User.objects.create_user(
            login='author', email='author@example.com', password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post', content='Content',
            author=self.author, status=Post.Status.MODERATION,
        )

    def test_create_moderation(self):
        ct = ContentType.objects.get_for_model(Post)
        mod = Moderation.objects.create(
            content_type=ct,
            object_id=self.post.pk,
            status=Moderation.Status.PENDING,
        )
        self.assertEqual(mod.status, Moderation.Status.PENDING)
        self.assertEqual(str(mod.content_object), self.post.title)

    def test_accept_moderation(self):
        ct = ContentType.objects.get_for_model(Post)
        mod = Moderation.objects.create(
            content_type=ct, object_id=self.post.pk,
        )
        mod.accept(moderator=self.moderator, comment='Looks good!')
        self.assertEqual(mod.status, Moderation.Status.ACCEPTED)
        self.assertEqual(mod.moderator, self.moderator)
        self.assertIsNotNone(mod.moderated_at)

    def test_decline_moderation(self):
        ct = ContentType.objects.get_for_model(Post)
        mod = Moderation.objects.create(
            content_type=ct, object_id=self.post.pk,
        )
        mod.decline(moderator=self.moderator, comment='Does not comply')
        self.assertEqual(mod.status, Moderation.Status.DECLINED)
        self.assertEqual(mod.moderator, self.moderator)
        self.assertIsNotNone(mod.moderated_at)

    def test_status_choices(self):
        self.assertIn('pending', [s[0] for s in Moderation.Status.choices])
        self.assertIn('accepted', [s[0] for s in Moderation.Status.choices])
        self.assertIn('declined', [s[0] for s in Moderation.Status.choices])


class ModerationAPITest(APITestCase):
    """Тесты API модерации."""

    def setUp(self):
        self.moderator = User.objects.create_superuser(
            login='moderator', email='mod@example.com', password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            login='admin', email='admin@example.com', password='adminpass123'
        )
        self.author = User.objects.create_user(
            login='author', email='author@example.com', password='testpass123'
        )
        self.regular_user = User.objects.create_user(
            login='user', email='user@example.com', password='testpass123'
        )
        self.post = Post.objects.create(
            title='Moderation Post', content='Content',
            author=self.author, status=Post.Status.MODERATION,
        )
        ct = ContentType.objects.get_for_model(Post)
        self.moderation = Moderation.objects.create(
            content_type=ct, object_id=self.post.pk,
        )

    def get_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_list_moderation_requires_auth(self):
        """Список модерации требует авторизации."""
        response = self.client.get('/api/moderation/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_moderation_regular_user(self):
        """Обычный пользователь не видит модерацию."""
        token = self.get_token(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/moderation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_list_moderation_moderator(self):
        """Модератор видит модерацию."""
        token = self.get_token(self.moderator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/moderation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_accept_moderation(self):
        """Принятие на модерацию."""
        token = self.get_token(self.moderator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/moderation/{self.moderation.pk}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.moderation.refresh_from_db()
        self.post.refresh_from_db()
        self.assertEqual(self.moderation.status, Moderation.Status.ACCEPTED)
        self.assertEqual(self.post.status, Post.Status.PUBLISHED)

    def test_decline_moderation(self):
        """Отклонение на модерации."""
        token = self.get_token(self.moderator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/moderation/{self.moderation.pk}/decline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.moderation.refresh_from_db()
        self.assertEqual(self.moderation.status, Moderation.Status.DECLINED)

    def test_accept_nonexistent(self):
        """Принятие несуществующей записи."""
        token = self.get_token(self.moderator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/moderation/999/accept/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_without_moderator_role(self):
        """Принятие без роли модератора."""
        token = self.get_token(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/moderation/{self.moderation.pk}/accept/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

