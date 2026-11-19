"""Аутентификация DRF: серверные JWT-сессии в Redis и гостевые токены."""
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings as jwt_settings

from . import redis_store

GUEST_SCHEME = 'guest'


def get_guest_token(request):
    """Достать токен из заголовка Authorization: Guest <token>."""
    header = request.META.get('HTTP_AUTHORIZATION', '')
    if not header:
        return None
    scheme, _, token = header.partition(' ')
    if scheme.lower() != GUEST_SCHEME or not token.strip():
        return None
    return token.strip()


class GuestAuthentication(authentication.BaseAuthentication):
    """Анонимный гостевой токен. Права пользователя не повышаются."""

    def authenticate(self, request):
        token = get_guest_token(request)
        if not token:
            return None
        try:
            visitor_id = redis_store.get_guest_visitor(token, touch=True)
        except Exception:
            # Redis недоступен — публичные страницы должны продолжать работать
            return None
        if not visitor_id:
            return None

        request.visitor_id = visitor_id
        request.guest_token = token
        request.is_guest = True
        return AnonymousUser(), None


class SessionJWTAuthentication(JWTAuthentication):
    """JWT с проверкой серверной сессии в Redis (мгновенный отзыв)."""

    def get_user(self, validated_token):
        sid = validated_token.get('sid')
        user_id = validated_token.get(jwt_settings.USER_ID_CLAIM)

        if not sid:
            raise InvalidToken(_('Токен не содержит идентификатор сессии'))

        try:
            valid = redis_store.session_exists(sid, user_id)
        except Exception as exc:
            raise exceptions.AuthenticationFailed(
                _('Сервис авторизации недоступен')
            ) from exc

        if not valid:
            raise InvalidToken(_('Сессия не найдена или отозвана. Войдите снова.'))

        return super().get_user(validated_token)
