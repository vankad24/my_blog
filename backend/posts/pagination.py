"""Пагинация списка постов."""
from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    """Главная страница грузит посты порциями по 4."""

    page_size = 4
