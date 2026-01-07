"""
Template tags for file handling
"""
from django import template
from your_app.services.file_storage import file_storage_service

register = template.Library()

@register.filter
def storage_url(file_path):
    """
    Get URL for a file based on environment
    
    Usage: {{ obj.front_page_photo|storage_url }}
    """
    if not file_path:
        return '#'
    return file_storage_service.get_file_url(file_path)

@register.filter
def file_exists(file_path):
    """
    Check if file exists in storage
    
    Usage: {% if obj.front_page_photo|file_exists %}
    """
    if not file_path:
        return False
    return file_storage_service.file_exists(file_path)

@register.filter
def file_size(file_path):
    """
    Get file size in human readable format
    
    Usage: {{ obj.front_page_photo|file_size }}
    """
    size_bytes = file_storage_service.get_file_size(file_path)
    
    if not size_bytes or size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1
    
    return f"{size_bytes:.1f} {units[unit_index]}"