from django.urls import path
from .views import backup

urlpatterns = [
    path('', backup, name='backup'),
]
