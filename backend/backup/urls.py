from django.urls import path
from .views import backup_db, backup_media

urlpatterns = [
    path('db/', backup_db, name='backup-db'),
    path('media/', backup_media, name='backup-media'),
]
