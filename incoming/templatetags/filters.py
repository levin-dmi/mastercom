from django import template

register = template.Library()


@register.filter
def currency(value):
    if value is None:
        return '???'
    if type(value) == str:
        return value
    if round(float(value), 2) == 0:
        return '0'
    return f"{float(value):_.2f}".replace("_", " ").replace('.', ',')


@register.filter
def get_obj_attr(obj, attr):
    return getattr(obj, attr)


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
