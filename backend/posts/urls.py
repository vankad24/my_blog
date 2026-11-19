from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostLikeView,
    PostViewCountView,
    LikedPostsListView,
    TagListView,
)

app_name = 'posts'

urlpatterns = [
    # Посты
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/liked/', LikedPostsListView.as_view(), name='liked-posts'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/like/', PostLikeView.as_view(), name='post-like'),
    path('posts/<int:pk>/view/', PostViewCountView.as_view(), name='post-view'),

    # Теги
    path('tags/', TagListView.as_view(), name='tag-list'),
]
