# reports/utils.py
from datetime import datetime, date, timedelta
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

def get_library_code(request):
    """Get library code from session"""
    return request.session.get('library_db', 'default')

def format_date_range(date_from, date_to=None):
    """Format date range for display"""
    if not date_from and not date_to:
        return ''
    
    if date_from and date_to:
        return f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}"
    elif date_from:
        return f"From {date_from.strftime('%d/%m/%Y')}"
    else:
        return f"Until {date_to.strftime('%d/%m/%Y')}"

def parse_date(date_str, default=None):
    """Parse date string to date object"""
    if not date_str:
        return default
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except (ValueError, TypeError):
            logger.warning(f"Unable to parse date: {date_str}")
            return default

def build_filter_query(filters, model_fields):
    """Build Q objects from filters"""
    query = Q()
    
    for field, value in filters.items():
        if not value:
            continue
            
        # Handle different filter types
        if field in model_fields:
            if isinstance(value, list):
                query &= Q(**{f"{field}__in": value})
            else:
                query &= Q(**{field: value})
        elif field.endswith('_from'):
            base_field = field.replace('_from', '')
            if base_field in model_fields:
                query &= Q(**{f"{base_field}__gte": parse_date(value)})
        elif field.endswith('_to'):
            base_field = field.replace('_to', '')
            if base_field in model_fields:
                query &= Q(**{f"{base_field}__lte": parse_date(value)})
        elif field.endswith('_contains'):
            base_field = field.replace('_contains', '')
            if base_field in model_fields:
                query &= Q(**{f"{base_field}__icontains": value})
    
    return query

def get_month_range(year, month):
    """Get date range for a specific month"""
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    
    start_date = date(year, month, 1)
    end_date = next_month - timedelta(days=1)
    
    return start_date, end_date

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "₹ 0.00"
    
    try:
        return f"₹ {float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₹ 0.00"

def truncate_text(text, length=100):
    """Truncate text with ellipsis"""
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    return text[:length] + "..."

def safe_int(value, default=0):
    """Safely convert to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default