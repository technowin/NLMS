from django import template

register = template.Library()
from django.utils.translation import get_language_info

@register.filter
def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

@register.filter(name='to_str')
def to_str(value):
    """Converts an integer to a string."""
    try:
        return str(value)
    except (ValueError, TypeError):
        return ""
    
@register.filter
def in_list(value, arg):
    """Check if value is in the provided list of integers."""
    try:
        # Convert the comma-separated string to a list of integers
        arg_list = [int(i) for i in arg.split(',')]
    except ValueError:
        return False
    return value in arg_list
    
@register.filter
def in_pairs(value):
    """Divide a list into pairs."""
    return [value[i:i+4] for i in range(0, len(value), 4)]

@register.filter
def replace_spaces(value):
    """Replace spaces with an empty string."""
    return value.replace(" ", "")

@register.filter
def is_long_text(value, length=50):
    return len(value) > length


@register.filter
def zip_lists(list1, list2):
    return zip(list1, list2)
   

@register.filter
def index(sequence, position):
    """Returns the item at the given index in the sequence."""
    try:
        return sequence[position]
    except IndexError:
        return None

@register.filter
def map(attribute_list, key):
    """Returns a list of values for a given key from a list of dictionaries."""
    return [d[key] for d in attribute_list if key in d]


from cryptography.fernet import Fernet
from django.conf import settings
import base64

def generate_key():
    return Fernet.generate_key()
def get_encryption_key():
    return settings.ENCRYPTION_KEY.encode()

@register.filter
def enc(parameter):
    cipher_suite = Fernet(get_encryption_key())
    cipher_text = cipher_suite.encrypt(parameter.encode())
    # Use base64 encoding to make the result shorter and more URL-friendly
    encoded_cipher_text = base64.urlsafe_b64encode(cipher_text).decode()
    return encoded_cipher_text

@register.filter
def dec(encoded_cipher_text):
    # Decode the base64-encoded string before decrypting
    cipher_text = base64.urlsafe_b64decode(encoded_cipher_text.encode())
    cipher_suite = Fernet(get_encryption_key())
    plain_text = cipher_suite.decrypt(cipher_text).decode()
    return plain_text

def trim(value):
    if isinstance(value, str):
        return value.strip()
    return value


# BOM Filters
@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def filter_by_status(items, status):
    return [item for item in items if item['status'] == status]


@register.filter
def natural_sort(items):
    """Sorts items by their sort_order field treating it as version numbers"""
    def sort_key(item):
        try:
            return [int(part) for part in item.sort_order.split('.')]
        except (ValueError, AttributeError):
            return []
    
    return sorted(items, key=sort_key)

@register.filter
def subtract1(value, arg):
    """Subtract the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return ''
        

@register.filter
def duration_format(value):
    """Convert duration to HH:MM:SS format"""
    if not value:
        return "00:00:00"
    
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@register.filter
def mul(value, arg):
    """Multiply the value by the arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    

@register.filter
def get_lowest_cost_supplier(component):
    return component.suppliers.filter(is_approved=True).order_by('cost').first()

@register.filter
def calculate_value(quantity, cost):
    try:
        return float(quantity) * float(cost)
    except (TypeError, ValueError):
        return 0
    

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg"""
    return float(value) * float(arg)

@register.filter
def language_name(code):
    try:
        return get_language_info(code)['name_local']
    except:
        return code
    

from itertools import groupby
from operator import attrgetter

@register.filter
def groupby_type(items):
    # Filter out items with empty type first
    filtered_items = [item for item in items if item.type]
    return groupby(sorted(filtered_items, key=attrgetter('type')), key=attrgetter('type'))

@register.filter
def increment(value):
    return value + 1

@register.filter(name='custom_truncate')
def custom_truncate(value, arg=50):
    if value is None:
        return ''
    
    try:
        length = int(arg)
    except ValueError:
        return value  # return original if arg is not an integer

    value = str(value)  # in case it's not a string

    if len(value) > length:
        return value[:length] + '...'
    return value

from datetime import date

@register.filter
def days_left(value):
    if not value:
        return None
    delta = value - date.today()
    return delta.days

@register.filter
def get_item(dictionary, key):
    """Custom template filter to get a dictionary value by key"""
    return dictionary.get(str(key))


@register.filter
def div(value, arg):
    """Divide value by arg."""
    try:
        return float(value) / float(arg) if arg else 0
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
    

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add or merge CSS class to a form field widget."""
    existing_classes = field.field.widget.attrs.get("class", "")
    new_classes = f"{existing_classes} {css_class}".strip()
    return field.as_widget(attrs={"class": new_classes})