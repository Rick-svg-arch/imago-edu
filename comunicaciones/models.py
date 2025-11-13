from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from taggit.managers import TaggableManager

class Publicacion(models.Model):
    ESTADO_BORRADOR = 'borrador'
    ESTADO_PUBLICADO = 'publicado'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_PUBLICADO, 'Publicado'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título de la Publicación")

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default=ESTADO_BORRADOR,
        verbose_name="Estado"
    )
    fecha_publicacion = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Publicación (o Programación)"
    )
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    anclado = models.BooleanField(
        default=False, 
        verbose_name="Anclar Publicación",
        help_text="Las publicaciones ancladas aparecerán primero en la lista."
    )
    etiquetas = TaggableManager(
        verbose_name="Etiquetas",
        help_text="Una lista de etiquetas separadas por comas. Ej: Eventos, Anuncios, Verano 2024",
        blank=True
    )

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        ordering = ['-anclado', '-fecha_publicacion']

    def __str__(self):
        return self.titulo

class BloqueContenido(models.Model):
    TIPO_BLOQUE = [
        ('texto', 'Texto Enriquecido'),
        ('imagen', 'Imagen'),
        ('embed', 'Video / Red Social'),
        ('cita', 'Cita Destacada'),
    ]
    
    TAMANIO_IMAGEN = [
        ('small', 'Pequeño (400px)'),
        ('medium', 'Mediano (600px)'),
        ('large', 'Grande (800px)'),
        ('full', 'Ancho completo'),
    ]
    
    ALINEACION_IMAGEN = [
        ('left', 'Izquierda'),
        ('center', 'Centro'),
        ('right', 'Derecha'),
    ]
    
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='bloques')
    tipo = models.CharField(max_length=10, choices=TIPO_BLOQUE, verbose_name="Tipo de Bloque")
    orden = models.PositiveIntegerField(default=0, help_text="Define el orden de los bloques.")
    
    # Campos flexibles; solo uno se usará dependiendo del 'tipo'
    contenido_texto = CKEditor5Field(config_name='default', blank=True, null=True)
    contenido_imagen = models.ImageField(upload_to='comunicaciones/bloques/', blank=True, null=True)
    tamanio_imagen = models.CharField(max_length=10, choices=TAMANIO_IMAGEN, default='medium', blank=True, null=True)
    alineacion_imagen = models.CharField(max_length=10, choices=ALINEACION_IMAGEN, default='center', blank=True, null=True)
    caption_imagen = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descripción de la imagen")
    contenido_embed = models.TextField(blank=True, null=True, help_text="Pega aquí el código 'embed' completo.")
    contenido_cita = models.TextField(blank=True, null=True, help_text="Texto de la cita.")
    autor_cita = models.CharField(max_length=100, blank=True, null=True, help_text="Autor de la cita (opcional).")

    class Meta:
        verbose_name = "Bloque de Contenido"
        verbose_name_plural = "Bloques de Contenido"
        ordering = ['orden']

    def __str__(self):
        return f"Bloque #{self.orden} ({self.get_tipo_display()}) para '{self.publicacion.titulo}'"