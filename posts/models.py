import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field

# Create your models here.
def ruta_banner_tema(instance, filename):
    """
    Genera ruta para banners de temas del foro.
    """
    extension = os.path.splitext(filename)[1]
    nombre_unico = f"{uuid.uuid4()}{extension}"
    return f'forum/{instance.categoria.slug}/{nombre_unico}'

def ruta_banner_respuesta(instance, filename):
    """
    Genera ruta para banners de respuestas del foro.
    """
    tema = instance.tema
    categoria = tema.categoria
    extension = os.path.splitext(filename)[1]
    nombre_unico = f"{uuid.uuid4()}{extension}"
    return f'forum/{categoria.slug}/{tema.pk}/replies/{nombre_unico}'

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Tema(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='temas')
    titulo = models.CharField(max_length=200)
    contenido = CKEditor5Field(config_name='default', blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    banner = models.ImageField(blank=True, upload_to=ruta_banner_tema)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = "Tema"
        verbose_name_plural = "Temas"
        ordering = ['-fecha_creacion']

class Respuesta(models.Model):
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='respuestas')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    contenido = CKEditor5Field(config_name='comments')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    banner = models.ImageField(blank=True, upload_to=ruta_banner_respuesta)

    def __str__(self):
        return f"Respuesta de {self.autor.username} en '{self.tema.titulo}'"

    class Meta:
        verbose_name = "Respuesta"
        verbose_name_plural = "Respuestas"
        ordering = ['fecha_creacion']