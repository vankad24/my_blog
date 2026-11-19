from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    GuestTokenView,
    RegisterView,
    LogoutView,
    RegistrationListView,
    RegistrationAcceptView,
    RegistrationDeclineView,
    UserProfileView,
    ProfileUpdateView,
    PasswordChangeView,
    PublicUserProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerifyView,
    EmailResendView,
)

app_name = 'users'

urlpatterns = [
    # Аутентификация
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('auth/guest/', GuestTokenView.as_view(), name='guest-token'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Заявки на регистрацию (модераторы и админы)
    path('registrations/', RegistrationListView.as_view(), name='registrations'),
    path('registrations/<int:pk>/accept/', RegistrationAcceptView.as_view(), name='registration-accept'),
    path('registrations/<int:pk>/decline/', RegistrationDeclineView.as_view(), name='registration-decline'),

    # Восстановление пароля
    path('auth/password/reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Верификация email
    path('auth/email/verify/', EmailVerifyView.as_view(), name='email-verify'),
    path('auth/email/resend/', EmailResendView.as_view(), name='email-resend'),

    # Профиль
    path('me/', UserProfileView.as_view(), name='me'),
    path('me/update/', ProfileUpdateView.as_view(), name='me-update'),
    path('me/password/', PasswordChangeView.as_view(), name='password-change'),

    # Публичный профиль
    path('users/<str:login>/', PublicUserProfileView.as_view(), name='public-profile'),
]
