from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Post, Tag, PostLike
from users.models import User


class TagModelTest(TestCase):
    """Тесты модели Tag."""

    def test_create_tag(self):
        tag = Tag.objects.create(name='python')
        self.assertEqual(tag.name, 'python')

    def test_tag_unique_name(self):
        Tag.objects.create(name='django')
        with self.assertRaises(Exception):
            Tag.objects.create(name='django')


class PostModelTest(TestCase):
    """Тесты модели Post."""

    def setUp(self):
        self.author = User.objects.create_user(
            login='author', email='author@example.com', password='testpass123'
        )
        self.tag = Tag.objects.create(name='python')

    def test_create_post(self):
        post = Post.objects.create(
            title='Test Post',
            content='Content here',
            author=self.author,
            status=Post.Status.PUBLISHED,
        )
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.status, Post.Status.PUBLISHED)
        self.assertEqual(str(post), 'Test Post')

    def test_posts_with_same_title(self):
        """Посты с одинаковым заголовком допустимы (ссылки по id)."""
        post1 = Post(title='Same Title', content='C1', author=self.author)
        post1.save()
        post2 = Post(title='Same Title', content='C2', author=self.author)
        post2.save()
        self.assertEqual(post1.title, post2.title)
        self.assertNotEqual(post1.pk, post2.pk)

    def test_post_tags(self):
        post = Post.objects.create(
            title='Post', content='Content', author=self.author
        )
        post.tags.add(self.tag)
        self.assertEqual(post.tags.count(), 1)
        self.assertTrue(post.tags.filter(name='python').exists())

    def test_soft_delete(self):
        from django.utils import timezone
        post = Post.objects.create(
            title='Post', content='Content', author=self.author
        )
        post.deleted_at = timezone.now()
        post.status = Post.Status.DRAFT
        post.save()
        self.assertIsNotNone(post.deleted_at)
        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_is_published_property(self):
        post = Post.objects.create(
            title='Post', content='Content', author=self.author,
            status=Post.Status.PUBLISHED,
        )
        self.assertTrue(post.is_published)

        draft = Post.objects.create(
            title='Draft', content='Content', author=self.author,
            status=Post.Status.DRAFT,
        )
        self.assertFalse(draft.is_published)

    def test_post_generic_relations(self):
        """GenericRelation для комментариев и модерации."""
        from comments.models import Comment
        from moderation.models import Moderation
        from django.contrib.contenttypes.models import ContentType

        post = Post.objects.create(
            title='Generic Relation Test',
            content='Content',
            author=self.author,
            status=Post.Status.PUBLISHED,
        )
        ct = ContentType.objects.get_for_model(Post)

        # Создаём комментарий через GenericRelation
        Comment.objects.create(
            body='Comment via generic relation',
            author=self.author,
            content_type=ct,
            object_id=post.pk,
        )
        # Проверяем, что он доступен через post.comments
        self.assertEqual(post.comments.count(), 1)

        # Создаём модерацию через GenericRelation
        Moderation.objects.create(
            content_type=ct,
            object_id=post.pk,
            status=Moderation.Status.PENDING,
        )
        self.assertEqual(post.moderations.count(), 1)


class PostLikeModelTest(TestCase):
    """Тесты модели PostLike."""

    def setUp(self):
        self.user = User.objects.create_user(login='user1', email='u1@test.com', password='test123456')
        self.user2 = User.objects.create_user(login='user2', email='u2@test.com', password='test123456')
        self.post = Post.objects.create(
            title='Test', content='Content', author=self.user,
            status=Post.Status.PUBLISHED,
        )

    def test_create_like(self):
        like = PostLike.objects.create(user=self.user2, post=self.post)
        self.assertEqual(like.user, self.user2)
        self.assertEqual(like.post, self.post)

    def test_unique_like(self):
        PostLike.objects.create(user=self.user2, post=self.post)
        with self.assertRaises(Exception):
            PostLike.objects.create(user=self.user2, post=self.post)

    def test_toggle_like(self):
        """Тоггл лайка."""
        like, created = PostLike.objects.get_or_create(user=self.user2, post=self.post)
        self.assertTrue(created)
        self.assertEqual(PostLike.objects.count(), 1)

        # Удаляем лайк
        like.delete()
        self.assertEqual(PostLike.objects.count(), 0)

        # Создаём снова
        like2, created2 = PostLike.objects.get_or_create(user=self.user2, post=self.post)
        self.assertTrue(created2)
        self.assertEqual(PostLike.objects.count(), 1)


class PostAPITest(APITestCase):
    """Тесты API для постов."""

    def setUp(self):
        self.author = User.objects.create_user(
            login='author', email='author@example.com', password='testpass123'
        )
        self.user = User.objects.create_user(
            login='reader', email='reader@example.com', password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            login='admin', email='admin@example.com', password='adminpass123'
        )
        self.tag = Tag.objects.create(name='python')
        self.post = Post.objects.create(
            title='Published Post',
            content='Published content',
            author=self.author,
            status=Post.Status.PUBLISHED,
        )
        self.post.tags.add(self.tag)

    def get_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_list_posts(self):
        """Список опубликованных постов."""
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Published Post')

    def test_list_posts_filter_by_tag(self):
        """Фильтрация по тегу."""
        response = self.client.get(f'/api/posts/?tag={self.tag.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_posts_search(self):
        """Поиск по заголовку."""
        response = self.client.get('/api/posts/?search=Published')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_post_detail(self):
        """Детальный просмотр поста."""
        response = self.client.get(f'/api/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Published Post')
        self.assertEqual(len(response.data['tags']), 1)

    def test_create_post_requires_auth(self):
        """Создание поста требует авторизации."""
        data = {
            'title': 'New Post',
            'content': 'New content',
        }
        response = self.client.post('/api/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post(self):
        """Создание поста авторизованным пользователем."""
        token = self.get_token(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'title': 'New Post',
            'content': 'New content',
        }
        response = self.client.post('/api/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)

    def test_create_post_without_title(self):
        """Заголовок генерируется из первой непустой строки контента."""
        token = self.get_token(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'content': '\n\n<p>Первая строка</p>\n<p>Вторая строка</p>',
        }
        response = self.client.post('/api/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.last()
        self.assertEqual(post.title, '<p>Первая строка</p>')

    def test_update_own_post(self):
        """Обновление своего поста."""
        token = self.get_token(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'title': 'Updated Title', 'content': 'Updated content'}
        response = self.client.put(f'/api/posts/{self.post.pk}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')

    def test_delete_own_post(self):
        """Удаление своего поста (мягкое)."""
        token = self.get_token(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.delete(f'/api/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertIsNotNone(self.post.deleted_at)

    def test_like_post(self):
        """Лайк поста."""
        token = self.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['liked'])

    def test_toggle_like(self):
        """Отмена лайка."""
        token = self.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Первый лайк
        response = self.client.post(f'/api/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Отмена лайка
        response = self.client.post(f'/api/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['liked'])

    def test_liked_posts(self):
        """Избранные посты."""
        token = self.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.client.post(f'/api/posts/{self.post.pk}/like/')
        response = self.client.get('/api/posts/liked/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_tags_list(self):
        """Список тегов."""
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_post_with_tags(self):
        """Создание поста с тегами."""
        token = self.get_token(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'title': 'Post with tags',
            'content': 'Content',
            'tags': [self.tag.pk],
        }
        response = self.client.post('/api/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.last()
        self.assertEqual(post.tags.count(), 1)