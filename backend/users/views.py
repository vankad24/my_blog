from rest_framework import status, permissions, generics
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from . import redis_store
from .authentication import get_guest_token
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserUpdateSerializer,
    PendingRegistrationSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    CustomTokenObtainPairSerializer,
    SessionRefreshToken,
)

User = get_user_model()

RATE_LIMIT_MESSAGE = 'Слишком много попыток, попробуйте позже'


def get_client_ip(request) -> str:
    """IP клиента с учётом прокси."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''


def get_attempt_identifiers(request):
    """Ключи для лимита попыток: IP и посетитель (пользователь / guest-токен)."""
    identifiers = []

    ip = get_client_ip(request)
    if ip:
        identifiers.append(f'ip:{ip}')

    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        identifiers.append(f'u:{user.pk}')
        return identifiers

    visitor_id = getattr(request, 'visitor_id', None)
    if not visitor_id:
        token = get_guest_token(request)
        if token:
            try:
                visitor_id = redis_store.get_guest_visitor(token)
            except Exception:
                visitor_id = None
    if visitor_id:
        identifiers.append(f'g:{visitor_id}')

    return identifiers


def check_auth_rate_limit(request, scope: str):
    """Вернуть Response 429, если лимит попыток превышен, иначе None."""
    try:
        for identifier in get_attempt_identifiers(request):
            allowed, retry_after = redis_store.hit_rate_limit(
                scope,
                identifier,
                settings.AUTH_RATE_LIMIT,
                settings.AUTH_RATE_WINDOW,
            )
            if not allowed:
                return Response(
                    {'detail': RATE_LIMIT_MESSAGE},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={'Retry-After': str(retry_after)},
                )
    except Exception:
        # Redis недоступен — не блокируем вход из-за лимитера
        return None
    return None


def reset_auth_rate_limit(request, scope: str) -> None:
    """Сбросить счётчик после успешной попытки."""
    try:
        for identifier in get_attempt_identifiers(request):
            redis_store.reset_rate_limit(scope, identifier)
    except Exception:
        pass


class CustomTokenObtainPairView(TokenObtainPairView):
    """Эндпоинт входа с расширенным JWT и лимитом попыток."""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        limited = check_auth_rate_limit(request, 'login')
        if limited is not None:
            return limited

        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            reset_auth_rate_limit(request, 'login')

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """Эндпоинт обновления токена."""

    pass


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя (требует подтверждения модератора)."""

    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        limited = check_auth_rate_limit(request, 'register')
        if limited is not None:
            return limited

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        reset_auth_rate_limit(request, 'register')

        return Response(
            {'message': 'Ожидайте подтверждения регистрации'},
            status=status.HTTP_201_CREATED,
        )


class RegistrationListView(generics.ListAPIView):
    """Заявки на регистрацию (только модераторы и админы)."""

    serializer_class = PendingRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_moderator:
            return User.objects.none()

        status_filter = self.request.query_params.get(
            'status', User.RegistrationStatus.PENDING
        )
        if status_filter not in User.RegistrationStatus.values:
            status_filter = User.RegistrationStatus.PENDING

        return User.objects.filter(
            registration_status=status_filter
        ).order_by('-created_at')


class RegistrationActionMixin:
    """Общая логика принятия/отклонения заявки на регистрацию."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PendingRegistrationSerializer

    def get_target(self, request, pk):
        if not request.user.is_moderator:
            return None, Response(
                {'error': 'Нет прав'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None, Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target.is_moderator:
            return None, Response(
                {'error': 'Нельзя изменить регистрацию модератора или администратора'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return target, None


class RegistrationAcceptView(RegistrationActionMixin, generics.GenericAPIView):
    """Подтвердить регистрацию пользователя."""

    def post(self, request, pk):
        target, error = self.get_target(request, pk)
        if error is not None:
            return error

        if target.registration_status == User.RegistrationStatus.APPROVED:
            return Response(
                {'message': 'Регистрация уже подтверждена'},
                status=status.HTTP_200_OK,
            )

        target.registration_status = User.RegistrationStatus.APPROVED
        target.save(update_fields=['registration_status', 'updated_at'])

        return Response(
            {
                'message': 'Регистрация подтверждена',
                'user': PendingRegistrationSerializer(target).data,
            },
            status=status.HTTP_200_OK,
        )


class RegistrationDeclineView(RegistrationActionMixin, generics.GenericAPIView):
    """Отклонить регистрацию пользователя."""

    def post(self, request, pk):
        target, error = self.get_target(request, pk)
        if error is not None:
            return error

        target.registration_status = User.RegistrationStatus.REJECTED
        target.save(update_fields=['registration_status', 'updated_at'])
        # Отзываем возможные активные сессии
        redis_store.invalidate_user_sessions(target.id)

        return Response(
            {
                'message': 'Регистрация отклонена',
                'user': PendingRegistrationSerializer(target).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(generics.GenericAPIView):
    """Выход из системы: отзыв серверной сессии в Redis."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = SessionRefreshToken(refresh_token)
        except TokenError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sid = token.payload.get('sid')
        if not sid:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Удаляем сессию — access и refresh перестают работать
        redis_store.delete_session(sid, request.user.id)
        return Response(
            {'message': 'Вы успешно вышли'},
            status=status.HTTP_200_OK,
        )


class GuestTokenView(generics.GenericAPIView):
    """Выдача гостевого токена. Доступен без авторизации.

    Если браузер не прислал токен (например, инкогнито с очищенным
    localStorage), посетитель восстанавливается по IP: выдаётся новый
    токен, но с тем же visitor_id.
    """

    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _remember_ip(ip, visitor_id):
        """Обновить связку IP -> visitor_id; счётчикам она не критична."""
        try:
            redis_store.remember_guest_visitor_for_ip(ip, visitor_id)
        except Exception:
            pass

    def post(self, request):
        ip = get_client_ip(request)
        token = getattr(request, 'guest_token', None)

        if token:
            visitor_id = redis_store.get_guest_visitor(token, touch=True)
            if visitor_id:
                self._remember_ip(ip, visitor_id)
                return Response(
                    {
                        'token': token,
                        'token_type': 'Guest',
                        'visitor_id': visitor_id,
                        'expires_in': settings.GUEST_TOKEN_TTL,
                    },
                    status=status.HTTP_200_OK,
                )

        # Токена нет или он недействителен — пробуем узнать посетителя по IP
        visitor_id = None
        if ip:
            try:
                visitor_id = redis_store.get_guest_visitor_by_ip(ip)
            except Exception:
                visitor_id = None

        token, visitor_id = redis_store.create_guest_session(visitor_id)
        self._remember_ip(ip, visitor_id)

        return Response(
            {
                'token': token,
                'token_type': 'Guest',
                'visitor_id': visitor_id,
                'expires_in': settings.GUEST_TOKEN_TTL,
            },
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveAPIView):
    """Профиль текущего пользователя."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileUpdateView(generics.UpdateAPIView):
    """Обновление профиля."""

    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(generics.GenericAPIView):
    """Смена пароля."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            request.user, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Отзываем все сессии пользователя: старые токены больше не действуют
        redis_store.invalidate_user_sessions(request.user.id)
        return Response(
            {'message': 'Пароль успешно изменён'},
            status=status.HTTP_200_OK,
        )


class PublicUserProfileView(generics.RetrieveAPIView):
    """Публичный профиль пользователя (по login)."""

    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'login'

    def get_queryset(self):
        return User.objects.all()


class PasswordResetRequestView(generics.GenericAPIView):
    """Запрос на восстановление пароля."""

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Генерируем токен для восстановления пароля
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # В разработке — выводим токен в ответ (в продакшене — отправляем email)
        if settings.DEBUG:
            reset_link = f"http://localhost:5173/reset-password?uid={uid}&token={token}"
            return Response(
                {
                    'message': 'Токен восстановления создан (DEBUG mode)',
                    'uid': uid,
                    'token': token,
                    'reset_link': reset_link,
                },
                status=status.HTTP_200_OK,
            )

        # В продакшене отправляем email
        # reset_link = f"https://yourdomain.com/reset-password?uid={uid}&token={token}"
        # send_mail(
        #     'Восстановление пароля',
        #     f'Перейдите по ссылке для восстановления: {reset_link}',
        #     'noreply@yourdomain.com',
        #     [email],
        #     fail_silently=False,
        # )

        return Response(
            {'message': 'Письмо с инструкциями отправлено на email'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """Подтверждение сброса пароля."""

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Сброс пароля инвалидирует все активные сессии
        redis_store.invalidate_user_sessions(user.id)

        return Response(
            {'message': 'Пароль успешно изменён'},
            status=status.HTTP_200_OK,
        )


class EmailVerifyView(generics.GenericAPIView):
    """Верификация email."""

    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                'message': 'Email успешно подтверждён',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class EmailResendView(generics.GenericAPIView):
    """Повторная отправка письма верификации."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.email_verified_at:
            return Response(
                {'message': 'Email уже подтверждён'},
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        if settings.DEBUG:
            verify_link = f"http://localhost:5173/verify-email?uid={uid}&token={token}"
            return Response(
                {
                    'message': 'Ссылка для верификации создана (DEBUG mode)',
                    'uid': uid,
                    'token': token,
                    'verify_link': verify_link,
                },
                status=status.HTTP_200_OK,
            )

        # В продакшене отправляем email
        # verify_link = f"https://yourdomain.com/verify-email?uid={uid}&token={token}"
        # send_mail(
        #     'Подтверждение email',
        #     f'Перейдите по ссылке для подтверждения: {verify_link}',
        #     'noreply@yourdomain.com',
        #     [user.email],
        #     fail_silently=False,
        # )

        return Response(
            {'message': 'Письмо с верификацией отправлено'},
            status=status.HTTP_200_OK,
        )

