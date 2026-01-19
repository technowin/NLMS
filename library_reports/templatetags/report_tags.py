# reports/templatetags/report_tags.py
from django import template

register = template.Library()


@register.inclusion_tag('reports/filters/select.html')
def render_select_filter(filter_config):
    return {
        'field': filter_config.get('field'),
        'options': filter_config.get('options', []),
    }


@register.inclusion_tag('reports/filters/date_range.html')
def render_date_range_filter(filter_config):
    return {
        'field': filter_config.get('field'),
    }


@register.simple_tag
def render_filter_widget(filter_config):
    """
    Dispatcher tag – decides which filter widget to render
    """
    widget_type = filter_config.get('type', 'text')

    if widget_type == 'select':
        return render_select_filter(filter_config)
    elif widget_type == 'date_range':
        return render_date_range_filter(filter_config)

    return ''
