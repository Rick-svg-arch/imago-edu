from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def render_content_with_attachment(context, documento):
    """
    Renderiza el contenido del documento, insertando el adjunto si se encuentra un placeholder.
    Si no, muestra el adjunto al final.
    """
    placeholder = '[ADJUNTO_AQUI]'
    content = documento.descripcion
    attachment_html = ""
    attachment_inserted = False

    # Primero, renderizamos el HTML del adjunto para tenerlo listo
    if documento.adjunto:
        attachment_html = render_to_string(
            'lecturas/_attachment_viewer.html', 
            {'documento': documento, 'request': context['request']}
        )

    # Si el placeholder existe en el contenido, lo reemplazamos
    if placeholder in content and documento.adjunto:
        content = content.replace(placeholder, attachment_html)
        attachment_inserted = True
    
    # Marcamos el contenido como seguro para que se renderice el HTML
    final_content = mark_safe(content)
    
    # Si el adjunto existe pero NO fue insertado, lo añadimos al final
    if documento.adjunto and not attachment_inserted:
        final_content += mark_safe(attachment_html)

    return final_content