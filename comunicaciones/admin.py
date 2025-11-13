from django.contrib import admin
from .models import Publicacion
from taggit.models import Tag

@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'fecha_publicacion')
    list_filter = ('autor',)
    search_fields = ('titulo', 'contenido')
    
    fieldsets = (
        (None, {
            'fields': ('titulo', 'autor')
        }),
        ('Contenido Tipo Noticia (Opcional)', {
            'description': 'Usa estos campos para crear un artículo o noticia.',
            'fields': ('imagen_destacada', 'contenido'),
        }),
        ('Contenido Embebido (Opcional)', {
            'description': 'Usa este campo para mostrar un video de YouTube, un tweet, etc. Simplemente pega el código para insertar/embeber.',
            'fields': ('codigo_embed',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.autor:
            obj.autor = request.user
        super().save_model(request, obj, form, change)