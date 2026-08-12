from django.urls import path
from .views import (
    ModerationListView,
    ModerationAcceptView,
    ModerationDeclineView,
)

app_name = 'moderation'

urlpatterns = [
    path('moderation/', ModerationListView.as_view(), name='moderation-list'),
    path('moderation/<int:pk>/accept/', ModerationAcceptView.as_view(), name='moderation-accept'),
    path('moderation/<int:pk>/decline/', ModerationDeclineView.as_view(), name='moderation-decline'),
]
