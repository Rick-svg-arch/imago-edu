from django import template
from comunicaciones.forms import BloqueTextoForm

register = template.Library()

@register.filter
def get_texto_form(bloque):
    """
    Retorna un formulario de BloqueTextoForm con la instancia del bloque cargada.
    Esto asegura que CKEditor se inicialice con el contenido existente.
    """
    return BloqueTextoForm(instance=bloque)