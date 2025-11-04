import os
import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
def ruta_banner_tema(instance, filename):
    extension = os.path.splitext(filename)[1]
    #Generar un nombre de archivo único usando un UUID
    nombre_unico = f"{uuid.uuid4()}{extension}"
    return f'forum/{instance.categoria.slug}/{nombre_unico}'

def ruta_banner_respuesta(instance, filename):
    tema = instance.tema
    categoria = tema.categoria
    # 1. Obtener la extensión del archivo original
    extension = os.path.splitext(filename)[1]
    # 2. Generar un nombre de archivo único con UUID
    nombre_unico = f"{uuid.uuid4()}{extension}"
    # 3. Construir la ruta completa y organizada
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
    # Un tema pertenece a una categoría
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='temas')
    
    titulo = models.CharField(max_length=200) # Título del tema/discusión
    contenido = models.TextField() # El post original
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
    # ... (sin cambios)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='respuestas')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    banner = models.ImageField(blank=True, upload_to=ruta_banner_respuesta)

    def __str__(self):
        return f"Respuesta de {self.autor.username} en '{self.tema.titulo}'"

    class Meta:
        verbose_name = "Respuesta"
        verbose_name_plural = "Respuestas"
        ordering = ['fecha_creacion']