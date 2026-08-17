from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя."""

    def create_user(self, login, email=None, name='', password=None, **extra_fields):
        if not login:
            raise ValueError('Login is required')
        email = self.normalize_email(email) or ''
        user = self.model(login=login, email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, email=None, name='', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(login, email, name, password, **extra_fields)


class User(AbstractUser):
    """Пользователь системы с поддержкой ролей."""

    objects = UserManager()  # type: ignore[assignment]

    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    username = None  # type: ignore[assignment]
    login = models.CharField('Логин', max_length=150, unique=True, db_index=True)
    email = models.EmailField('Email', unique=True)
    name = models.CharField('Имя', max_length=150, blank=True, default='')
    role = models.CharField(
        'Роль',
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
    )
    email_verified_at = models.DateTimeField('Email подтверждён', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['email', 'name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.login or self.email or str(self.id)

    @property
    def is_moderator(self) -> bool:
        return self.role in (self.Role.MODERATOR, self.Role.ADMIN)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN
