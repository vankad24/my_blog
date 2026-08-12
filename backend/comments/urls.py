from django.urls import path
from .views import CommentListView, CommentDetailView

app_name = 'comments'

urlpatterns = [
    path('comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]
