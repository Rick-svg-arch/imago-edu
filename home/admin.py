from django.contrib import admin
from .models import HomePageBlock, HeroConfiguration
from adminsortable2.admin import SortableAdminMixin

@admin.register(HeroConfiguration)
class HeroConfigurationAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'subtitulo')
    
    def has_add_permission(self, request):
        return not HeroConfiguration.objects.exists()

@admin.register(HomePageBlock)
class HomePageBlockAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('titulo', 'tipo_bloque', 'activo', 'orden')
    list_filter = ('tipo_bloque', 'activo')
    search_fields = ('titulo', 'contenido')
    list_display_links = ('titulo',)

    fieldsets = (
        (None, {
            'fields': (
                ('tipo_bloque', 'posicion_contenido'), 
                'titulo', 
                'activo'
            )
        }),
        ('Contenido Principal', {
            'fields': ('contenido',)
        }),
        ('Configuración para Bloques con Fondo', {
            'classes': ('collapse',),
            # El campo de posición ya no está aquí.
            'fields': ('imagen_fondo',) 
        }),
        ('Botones de Acción (Opcional)', {
            'classes': ('collapse',),
            'description': 'Puedes añadir hasta dos botones a cualquier bloque.',
            'fields': (
                ('enlace_texto_1', 'enlace_url_1', 'enlace_estilo_1', 'enlace_nueva_pestana_1'),
                ('enlace_texto_2', 'enlace_url_2', 'enlace_estilo_2', 'enlace_nueva_pestana_2'),
            )
        }),
    )

    class Media:
        css = {
            'all': ('css/vendors/_ckeditor5_styles.css',)
        }