"""
Template tags for file handling
"""
from django import template
from services.file_storage_service import FileStorageService

register = template.Library()

# Create global instance
file_service = FileStorageService()

@register.simple_tag
def get_file_url(file_path):
    """
    Template tag to get file URL
    
    Usage in template:
    {% load file_tags %}
    <a href="{% get_file_url document.file_path %}">View</a>
    """
    return file_service.get_file_url(file_path)

@register.filter
def file_url(file_path):
    """
    Template filter to get file URL
    
    Usage in template:
    {% load file_tags %}
    <a href="{{ document.file_path|file_url }}">View</a>
    """
    return file_service.get_file_url(file_path)

@register.filter
def file_exists(file_path):
    """
    Check if file exists
    
    Usage:
    {% if document.file_path|file_exists %}
        File exists
    {% endif %}
    """
    return file_service.file_exists(file_path)

@register.filter
def file_size_human(file_path):
    """
    Get human readable file size
    
    Usage:
    {{ document.file_path|file_size_human }}
    """
    size_bytes = file_service.get_file_size(file_path)
    
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

@register.filter(name='storage_url')
def storage_url_filter(file_path):
    """
    Template filter to get file URL for any environment
    Usage: {{ obj.front_page_photo|storage_url }}
    """
    if not file_path:
        return '#'
    return FileStorageService.get_file_url(file_path)

@register.filter(name='file_exists')
def file_exists_filter(file_path):
    """
    Check if file exists in storage
    Usage: {% if obj.front_page_photo|file_exists %}
    """
    if not file_path:
        return False
    return FileStorageService.file_exists(file_path)