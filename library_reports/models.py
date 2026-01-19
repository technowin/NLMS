# reports/models.py
from django.db import models
from django.contrib.postgres.fields import JSONField  # Use JSONField for MySQL too
import json

class ReportConfiguration(models.Model):
    REPORT_TYPES = [
        ('member', 'Member Report'),
        ('book', 'Book Report'),
        ('financial', 'Financial Report'),
        ('circulation', 'Circulation Report'),
        ('custom', 'Custom Report'),
    ]
    
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('select', 'Select'),
        ('multi_select', 'Multi-Select'),
        ('date_range', 'Date Range'),
        ('number_range', 'Number Range'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    base_model = models.CharField(max_length=255, help_text="Django model path, e.g., 'L01.models.MembershipDetails'")
    
    # JSON fields for configuration
    tabs = models.JSONField(default=list, help_text="List of tab configurations")
    filters = models.JSONField(default=dict, help_text="Filter configurations")
    columns = models.JSONField(default=list, help_text="Column configurations")
    default_settings = models.JSONField(default=dict, help_text="Default settings for the report")
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'tbl_report_configuration'
        ordering = ['report_type', 'name']
        verbose_name = 'Report Configuration'
        verbose_name_plural = 'Report Configurations'
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    def get_tabs_count(self):
        return len(self.tabs) if self.tabs else 0
    
    def get_filters_count(self):
        return len(self.filters) if isinstance(self.filters, dict) else 0
    
    def get_columns_count(self):
        return len(self.columns) if self.columns else 0
    
    def validate_configuration(self):
        """Validate the JSON configuration"""
        errors = []
        
        try:
            # Validate tabs
            if not isinstance(self.tabs, list):
                errors.append("Tabs must be a list")
            
            # Validate filters
            if not isinstance(self.filters, dict):
                errors.append("Filters must be a dictionary")
            
            # Validate columns
            if not isinstance(self.columns, list):
                errors.append("Columns must be a list")
            
            return errors
        except Exception as e:
            return [f"Configuration validation error: {str(e)}"]
    
    def get_preview_data(self):
        """Get preview data for the configuration"""
        return {
            'id': self.id,
            'name': self.name,
            'report_type': self.report_type,
            'report_type_display': self.get_report_type_display(),
            'tabs_count': self.get_tabs_count(),
            'filters_count': self.get_filters_count(),
            'columns_count': self.get_columns_count(),
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M'),
        }
    
    def get_available_models(self):
        """Get available models for selection"""
        # This would be populated dynamically from Django apps
        return [
            {'value': 'L01.models.MembershipDetails', 'label': 'Membership Details'},
            {'value': 'L01.models.MembershipDetailsHistory', 'label': 'Membership History'},
            {'value': 'L01.models.BookCatalog', 'label': 'Book Catalog'},
            {'value': 'L01.models.CirculationTransaction', 'label': 'Circulation Transaction'},
            {'value': 'L01.models.PaymentDetails', 'label': 'Payment Details'},
            {'value': 'L01.models.MemberEntryExit', 'label': 'Member Entry/Exit'},
            {'value': 'L01.models.MemberScreenActivity', 'label': 'Member Screen Activity'},
        ]
    
    def get_field_type_options(self):
        """Get field type options for filters and columns"""
        return [
            {'value': 'text', 'label': 'Text Field'},
            {'value': 'number', 'label': 'Number Field'},
            {'value': 'date', 'label': 'Date Field'},
            {'value': 'select', 'label': 'Dropdown Select'},
            {'value': 'multi_select', 'label': 'Multi-Select Dropdown'},
            {'value': 'date_range', 'label': 'Date Range'},
            {'value': 'number_range', 'label': 'Number Range'},
            {'value': 'checkbox', 'label': 'Checkbox'},
            {'value': 'radio', 'label': 'Radio Button'},
            {'value': 'hidden', 'label': 'Hidden Field'},
        ]
    
    def get_render_type_options(self):
        """Get render type options for columns"""
        return [
            {'value': 'text', 'label': 'Plain Text'},
            {'value': 'currency', 'label': 'Currency (₹)'},
            {'value': 'percentage', 'label': 'Percentage (%)'},
            {'value': 'date', 'label': 'Date Format'},
            {'value': 'datetime', 'label': 'Date-Time Format'},
            {'value': 'boolean', 'label': 'Yes/No'},
            {'value': 'badge', 'label': 'Badge'},
            {'value': 'button', 'label': 'Action Button'},
            {'value': 'link', 'label': 'Clickable Link'},
        ]