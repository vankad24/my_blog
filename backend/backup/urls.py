from django.urls import path
from .views import backup

urlpatterns = [
    path('db/', backup, name='backup-db'),
]
