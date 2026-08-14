from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Comment
from posts.models import Post
from users.models import User


class CommentModelTest(TestCase):
    """Тесты модели Comment."""

    def setUp(self):
        self.author = User.objects.create_user(
            login='author', email='author@example.com', password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post', content='Content',
            author=self.author, status=Post.Status.PUBLISHED,
        )

    def test_create_comment(self):
        comment = Comment.objects.create(
            body='Great post!',
            author=self.author,
            comment_object=self.post,
        )
        self.assertEqual(comment.body, 'Great post!')
        self.assertEqual(comment.author, self.author)
        self.assertEqual(str(comment), f"Comment by {self.author} on {self.post}")

    def test_comment_replies(self):
        """Комментарии с replies."""
        parent = Comment.objects.create(
            body='Parent comment',
            author=self.author,
            comment_object=self.post,
        )
        reply = Comment.objects.create(
            body='Reply',
            author=self.author,
            comment_object=self.post,
            parent=parent,
        )
        self.assertEqual(parent.replies.count(), 1)
        self.assertEqual(parent.replies.first(), reply)

    def test_soft_delete(self):
        """Мягкое удаление комментария."""
        comment = Comment.objects.create(
            body='Comment',
            author=self.author,
            comment_object=self.post,
        )
        self.assertFalse(comment.is_deleted)

        from django.utils import timezone
        comment.deleted_at = timezone.now()
        comment.save()
        self.assertTrue(comment.is_deleted)

    def test_replies_count(self):
        """Подсчёт ответов."""
        parent = Comment.objects.create(
            body='Parent',
            author=self.author,
            comment_object=self.post,
        )
        Comment.objects.create(
            body='Reply 1', author=self.author,
            comment_object=self.post, parent=parent,
        )
        Comment.objects.create(
            body='Reply 2', author=self.author,
            comment_object=self.post, parent=parent,
        )
        self.assertEqual(parent.replies_count, 2)


class CommentAPITest(APITestCase):
    """Тесты API для комментариев."""

    def setUp(self):
        self.author = User.objects.create_user(
            login='author', email='author@example.com', password='testpass123'
        )
        self.user = User.objects.create_user(
            login='commenter', email='commenter@example.com', password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post', content='Content',
            author=self.author, status=Post.Status.PUBLISHED,
        )
        self.ct = ContentType.objects.get_for_model(Post)

    def get_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_list_comments(self):
        """Список комментариев."""
        Comment.objects.create(
            body='Comment 1', author=self.author,
            comment_object=self.post,
        )
        response = self.client.get(
            f'/api/comments/?content_type=posts.post&object_id={self.post.pk}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_comment_requires_auth(self):
        """Создание комментария требует авторизации."""
        data = {
            'body': 'New comment',
            'content_type_str': 'posts.post',
            'object_id': self.post.pk,
        }
        response = self.client.post('/api/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment(self):
        """Создание комментария."""
        token = self.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'body': 'My comment',
            'content_type_str': 'posts.post',
            'object_id': self.post.pk,
        }
        response = self.client.post('/api/comments/', data, format='json')
        if response.status_code != 201:
            print('DEBUG: response.data =', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_create_reply(self):
        """Создание ответа на комментарий."""
        token = self.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        parent = Comment.objects.create(
            body='Parent', author=self.author, comment_object=self.post,
        )
        data = {
            'body': 'Reply',
            'content_type_str': 'posts.post',
            'object_id': self.post.pk,
            'parent': parent.pk,
        }
        response = self.client.post('/api/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.last()
        self.assertEqual(comment.parent, parent)

