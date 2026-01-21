# reports/models.py
from django.db import models
from django.utils import timezone
from L01.models import *
# reports/models.py - ENHANCE MODELS

class ReportSession(models.Model):
    """Store report configurations and filters"""
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=[
        ('member', 'Member Report'),
        ('book', 'Book Report'),
        ('financial', 'Financial Report'),
        ('circulation', 'Circulation Report')
    ])
    filters_json = models.JSONField(default=dict)
    selected_members_json = models.JSONField(default=list)
    tab_filters_json = models.JSONField(default=dict)  # Store filters for each tab
    
    # Additional fields for better organization
    description = models.TextField(null=True, blank=True)
    tags = models.CharField(max_length=500, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        CustomUser,
        related_name='shared_reports',
        blank=True
    )
    
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "tbl_report_session"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by', 'report_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"

class ReportExport(models.Model):
    """Track report exports"""
    session = models.ForeignKey(ReportSession, on_delete=models.CASCADE, null=True, blank=True)
    export_type = models.CharField(max_length=50, choices=[
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('print', 'Print')
    ])
    file_name = models.CharField(max_length=500)
    file_path = models.CharField(max_length=500, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # in bytes
    filters_applied = models.JSONField(default=dict)
    
    # Additional metadata
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    generation_time = models.FloatField(default=0)  # in seconds
    
    exported_at = models.DateTimeField(auto_now_add=True)
    exported_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = "tbl_report_export"
        ordering = ['-exported_at']
        indexes = [
            models.Index(fields=['exported_by', 'exported_at']),
        ]
    
    def __str__(self):
        return f"{self.file_name} ({self.export_type})"

class ReportSchedule(models.Model):
    """Schedule automatic report generation"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    filters_json = models.JSONField(default=dict)
    
    # Schedule settings
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Delivery settings
    email_recipients = models.TextField(null=True, blank=True)  # Comma-separated emails
    save_to_path = models.CharField(max_length=500, null=True, blank=True)
    
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "tbl_report_schedule"
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"