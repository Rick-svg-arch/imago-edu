from django.contrib import admin
from .models import Categoria, Tema, Respuesta

# Register your models here.
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}

class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'autor', 'fecha_creacion')
    list_filter = ('categoria', 'autor')

admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Tema, TemaAdmin)
admin.site.register(Respuesta)