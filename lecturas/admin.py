from django.contrib import admin
from .models import Documento, Genero, Autor

# Register your models here.
@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    search_fields = ('nombre',)

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'idioma', 'grado', 'autor_principal', 'nivel_dificultad', 'author', 'date')
    list_filter = ('grado', 'idioma', 'nivel_dificultad', 'generos', 'autor_principal')
    search_fields = ('titulo', 'descripcion', 'autor_principal__nombre')