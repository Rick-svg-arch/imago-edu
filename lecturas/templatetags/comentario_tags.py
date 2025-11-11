from django import template
from lecturas.forms import ComentarioForm

register = template.Library()

@register.simple_tag
def get_comentario_form():
    """Retorna una nueva instancia del formulario de comentarios"""
    return ComentarioForm()