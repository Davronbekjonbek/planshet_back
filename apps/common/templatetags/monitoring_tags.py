from django import template
import json
import pdb
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def pdb(value):
    """Convert a JSON string to Python dictionary"""
    return json.loads(value)

@register.filter
def index(value, arg):
    """Get an item from a list by index"""
    try:
        return value[arg]
    except (IndexError, TypeError, KeyError):
        return None

@register.filter
def average(value):
    """Calculate average of a list of numbers"""
    try:
        return sum(value) / len(value)
    except (TypeError, ZeroDivisionError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return 0

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return value / arg
    except (TypeError, ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0

@register.filter
def get_status_badge(status):
    """Return a formatted status badge"""
    status_classes = {
        'mavjud': 'success',
        'chegirma': 'warning',
        'mavsumiy': 'danger',
        'vaqtinchalik': 'info',
        'sotilmayapti': 'secondary',
        'obyekt_yopilgan': 'dark'
    }
    
    status_label = {
        'mavjud': 'Mahsulot mavjud',
        'chegirma': 'Chegirma asosida',
        'mavsumiy': 'Mavsumiy mahsulot',
        'vaqtinchalik': 'Vaqtincha mavjud emas',
        'sotilmayapti': 'Sotilmayapti',
        'obyekt_yopilgan': 'Obyekt yopilgan'
    }
    
    css_class = status_classes.get(status, 'secondary')
    label = status_label.get(status, status.capitalize())
    
    return mark_safe(f'<span class="badge bg-{css_class}">{label}</span>')

@register.simple_tag
def get_icon_color(icon_name, default_color='#BDBDBD'):
    """Get color code for icon based on icon name"""
    icon_colors = {
        'restaurant': '#FF7043',
        'water': '#039BE5',
        'flash': '#FDD835',
        'shirt': '#BA68C8',
        'bed': '#8D6E63',
        'cart': '#4CAF50',
        'eye': '#00ACC1',
        'leaf': '#558B2F',
        'construct': '#FFA000',
        'home': '#43A047',
        'briefcase': '#546E7A',
        'storefront': '#8E24AA',
        'car': '#616161',
        'tv': '#3949AB',
        'school': '#1E88E5',
        'person': '#F06292',
        'people': '#6D4C41',
        'nutrition': '#66BB6A',
        'location': '#BDBDBD'
    }
    return icon_colors.get(icon_name, default_color)
