from django.contrib import admin
from .models import Tag, Post, PostLike


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'views', 'likes_count', 'published_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['slug', 'views', 'likes_count', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
