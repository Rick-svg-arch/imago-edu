from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    Uso en la plantilla: {{ user|has_group:"NombreDelGrupo" }}
    """
    if user.is_authenticated:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            return False
        
        return group in user.groups.all()
    
    return False

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Toma la URL actual y reemplaza/añade los parámetros GET proporcionados.
    Uso: {% query_transform page=page_obj.next_page_number %}
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return query.urlencode()