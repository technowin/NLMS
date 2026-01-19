# reports/admin.py
from django.contrib import admin
from .models import ReportConfiguration

@admin.register(ReportConfiguration)
class ReportConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_active', 'created_at')
    list_filter = ('report_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('report_type', 'name', 'description', 'is_active')
        }),
        ('Configuration', {
            'fields': ('base_model', 'tabs', 'filters', 'columns')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )