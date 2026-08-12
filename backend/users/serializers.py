from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для чтения."""

    class Meta:
        model = User
        fields = ['id', 'login', 'name', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации."""

    password = serializers.CharField(write_only=True, min_length=8, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['login', 'email', 'name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля."""

    class Meta:
        model = User
        fields = ['name', 'email']

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Этот email уже занят')
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Пароли не совпадают'})
        return data

    def validate_old_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль')
        return value

    def save(self, **kwargs):
        self.instance.set_password(self.validated_data['new_password'])
        self.instance.save()
        return self.instance


class PasswordResetRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса на восстановление пароля."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email не найден')
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения сброса пароля."""

    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Пароли не совпадают'})
        return data

    def validate_uid(self, value):
        try:
            force_str(urlsafe_base64_decode(value))
        except (TypeError, ValueError, UnicodeDecodeError):
            raise serializers.ValidationError('Неверный UID токена')
        return value

    def save(self):
        try:
            uid = self.validated_data['uid']
            token = self.validated_data['token']
            new_password = self.validated_data['new_password']

            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return user
            else:
                raise serializers.ValidationError('Токен восстановления просрочен')
        except (TypeError, ValueError, UnicodeDecodeError):
            raise serializers.ValidationError('Неверный токен или UID')


class EmailVerificationSerializer(serializers.Serializer):
    """Сериализатор для верификации email."""

    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
            if not default_token_generator.check_token(user, data['token']):
                raise serializers.ValidationError('Токен верификации просрочен')
            self.validated_user = user
        except (TypeError, ValueError, UnicodeDecodeError):
            raise serializers.ValidationError('Неверный токен или UID')
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')
        return data

    def save(self):
        user = self.validated_user
        if not user.email_verified_at:
            from django.utils import timezone
            user.email_verified_at = timezone.now()
            user.save(update_fields=['email_verified_at'])
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для JWT с данными пользователя."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['login'] = user.login
        token['role'] = user.role
        return token
