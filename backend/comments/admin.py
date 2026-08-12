from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'body_preview', 'content_type', 'object_id', 'is_deleted', 'created_at']
    list_filter = ['created_at', 'deleted_at']
    search_fields = ['body', 'author__login']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Текст')
    def body_preview(self, obj):
        return obj.body[:100] + ('...' if len(obj.body) > 100 else '')
