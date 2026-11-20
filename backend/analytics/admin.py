from django.contrib import admin

from .models import SiteVisitCounter


@admin.register(SiteVisitCounter)
class SiteVisitCounterAdmin(admin.ModelAdmin):
    list_display = ['id', 'total', 'updated_at']
    readonly_fields = ['id', 'updated_at']
