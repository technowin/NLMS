# reports/admin.py - COMPLETE ADMIN INTERFACE

from django.contrib import admin
from django.utils.html import format_html
from .models import ReportSession, ReportExport, ReportSchedule

@admin.register(ReportSession)
class ReportSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'created_at', 'filter_count', 'is_public']
    list_filter = ['report_type', 'is_public', 'created_at']
    search_fields = ['name', 'created_by__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'description', 'tags', 'is_public')
        }),
        ('Filter Data', {
            'fields': ('filters_json', 'selected_members_json', 'tab_filters_json'),
            'classes': ('collapse',)
        }),
        ('Sharing', {
            'fields': ('shared_with',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def filter_count(self, obj):
        return len(obj.filters_json) if obj.filters_json else 0
    filter_count.short_description = 'Filter Count'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'export_type', 'exported_by', 'exported_at', 'file_size_display', 'row_count']
    list_filter = ['export_type', 'exported_at']
    search_fields = ['file_name', 'exported_by__username', 'transaction_id']
    readonly_fields = ['exported_at', 'generation_time']
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "N/A"
    file_size_display.short_description = 'File Size'

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'next_run', 'last_run']
    list_filter = ['frequency', 'is_active', 'report_type']
    search_fields = ['name', 'email_recipients']
    readonly_fields = ['created_at', 'updated_at', 'last_run']
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)