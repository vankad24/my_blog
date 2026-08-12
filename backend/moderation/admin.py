from django.contrib import admin
from .models import Moderation


@admin.register(Moderation)
class ModerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_type', 'object_id', 'status', 'moderator', 'moderated_at', 'created_at']
    list_filter = ['status', 'moderator', 'created_at']
    search_fields = ['comment']
    readonly_fields = ['created_at', 'moderated_at']
