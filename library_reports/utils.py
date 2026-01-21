# reports/utils.py
import os
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connections
import pandas as pd

def get_library_connection(library_code):
    """Get database connection for specific library"""
    if library_code in connections.databases:
        return connections[library_code]
    return connections['default']

def generate_excel_report(data, sheet_name, output_path):
    """Generate Excel report from data"""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet, sheet_data in data.items():
            df = pd.DataFrame(sheet_data)
            df.to_excel(writer, sheet_name=sheet, index=False)
    
    return output_path

def apply_date_filters(queryset, date_field, from_date, to_date):
    """Apply date range filters to queryset"""
    if from_date:
        queryset = queryset.filter(**{f'{date_field}__gte': from_date})
    if to_date:
        queryset = queryset.filter(**{f'{date_field}__lte': to_date})
    return queryset

def format_decimal(value):
    """Format decimal values for display"""
    if value is None:
        return '0.00'
    try:
        return f'{float(value):.2f}'
    except:
        return str(value)
    
# reports/utils.py - ADD MISSING UTILITY FUNCTIONS

import re
from datetime import datetime, timedelta
from django.utils import timezone
import unicodedata

def normalize_text(text):
    """Normalize text for search"""
    if not text:
        return ''
    # Convert to lowercase and remove accents
    text = str(text).lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text

def apply_member_details_filters(qs, filters):
    """Apply member details filters to queryset"""
    if filters.get('membership_month_from'):
        try:
            from_date = datetime.strptime(filters['membership_month_from'], '%Y-%m')
            qs = qs.filter(from_date__year=from_date.year, from_date__month=from_date.month)
        except:
            pass
    
    if filters.get('membership_month_to'):
        try:
            to_date = datetime.strptime(filters['membership_month_to'], '%Y-%m')
            qs = qs.filter(to_date__year=to_date.year, to_date__month=to_date.month)
        except:
            pass
    
    if filters.get('membership_type'):
        membership_type_ids = [int(id) for id in filters['membership_type'] if id.isdigit()]
        if membership_type_ids:
            qs = qs.filter(membership_id__in=membership_type_ids)
    
    if filters.get('ward'):
        qs = qs.filter(ward__icontains=filters['ward'])
    
    if filters.get('status'):
        status_values = [int(s) for s in filters['status']]
        qs = qs.filter(isactive__in=status_values)
    
    if filters.get('renewal_due_month'):
        try:
            due_month = datetime.strptime(filters['renewal_due_month'], '%Y-%m')
            qs = qs.filter(to_date__year=due_month.year, to_date__month=due_month.month)
        except:
            pass
    
    if filters.get('member_type'):
        member_type_ids = [int(id) for id in filters['member_type'] if id.isdigit()]
        if member_type_ids:
            qs = qs.filter(member_type_id__in=member_type_ids)
    
    return qs

def calculate_age(dob):
    """Calculate age from date of birth"""
    if not dob:
        return None
    today = timezone.now().date()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "₹0.00"
    try:
        return f"₹{float(amount):,.2f}"
    except:
        return f"₹{amount}"

def get_month_name(month_number):
    """Get month name from month number"""
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    if 1 <= month_number <= 12:
        return months[month_number - 1]
    return ''

def generate_report_filename(report_type, extension='xlsx'):
    """Generate filename for report export"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{report_type}_report_{timestamp}.{extension}"