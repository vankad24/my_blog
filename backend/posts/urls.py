from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostLikeView,
    LikedPostsListView,
    TagListView,
)

app_name = 'posts'

urlpatterns = [
    # Посты
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/liked/', LikedPostsListView.as_view(), name='liked-posts'),
    path('posts/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<slug:slug>/like/', PostLikeView.as_view(), name='post-like'),

    # Теги
    path('tags/', TagListView.as_view(), name='tag-list'),
]
