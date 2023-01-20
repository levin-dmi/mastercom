from django import template

register = template.Library()


@register.filter
def currency(value):
    if value is None or value == '':
        return ''
    if round(float(value), 2) == 0:
        return '0'
    return f"{float(value):_.2f}".replace("_", " ").replace('.', ',')

