from django.contrib import admin, auth
from .models import User

# Register your models here.


@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):
    list_display = ['login', 'email', 'name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['login', 'email', 'name']
    fieldsets = (
        (None, {'fields': ('login', 'password')}),
        ('Personal info', {'fields': ('name', 'email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'email_verified_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('login', 'email', 'name', 'password1', 'password2'),
        }),
    )
    ordering = ['-created_at']
