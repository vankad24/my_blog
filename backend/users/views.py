from rest_framework import status, permissions, generics
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Эндпоинт входа с расширенным JWT."""

    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """Эндпоинт обновления токена."""

    pass


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""

    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Отправляем письмо с подтверждением email
        # TODO: реализовать отправку email

        return Response(
            {'message': 'Пользователь успешно зарегистрирован'},
            status=status.HTTP_201_CREATED,
        )


class LogoutView(generics.GenericAPIView):
    """Выход из системы (черный список токена)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Вы успешно вышли'},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
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
        serializer.save()

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

