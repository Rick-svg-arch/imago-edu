from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
def ruta_de_subida(instance, filename):
    """
    Genera la ruta de subida para archivos adjuntos de documentos.
    Usa la fecha actual en lugar de instance.date para evitar errores con auto_now_add.
    """
    fecha_actual = timezone.now()
    return f'uploads/{instance.idioma}/{instance.grado}/{fecha_actual.year}/{fecha_actual.month}/{filename}'

def ruta_imagenes(instance, filename):
    """
    Genera la ruta de subida para imágenes de documentos.
    """
    fecha_actual = timezone.now()
    return f'uploads/{instance.idioma}/{instance.grado}/{fecha_actual.year}/{fecha_actual.month}/images/{filename}'

def ruta_subida_comentario(instance, filename):
    """
    Genera la ruta de subida para archivos adjuntos de comentarios.
    Usa la fecha del documento o la fecha actual si no está disponible.
    """
    documento = instance.documento
    
    # Usar la fecha del documento si existe, sino usar fecha actual
    if documento.date:
        fecha_ref = documento.date
    else:
        fecha_ref = timezone.now()
    
    ruta_base_documento = (
        f'uploads/{documento.idioma}/{documento.grado}/'
        f'{fecha_ref.year}/{fecha_ref.month}'
    )
    return f'{ruta_base_documento}/comentarios/{filename}'

def ruta_imagenes_comentario(instance, filename):
    """
    Genera la ruta de subida para imágenes de comentarios.
    """
    documento = instance.documento
    
    # Usar la fecha del documento si existe, sino usar fecha actual
    if documento.date:
        fecha_ref = documento.date
    else:
        fecha_ref = timezone.now()
    
    ruta_base_documento = (
        f'uploads/{documento.idioma}/{documento.grado}/'
        f'{fecha_ref.year}/{fecha_ref.month}'
    )
    return f'{ruta_base_documento}/comentarios/images/{filename}'

ELEGIR_GRADO = [
        ('sexto', 'Sexto'),
        ('septimo', 'Séptimo'),
        ('octavo', 'Octavo'),
        ('noveno', 'Noveno'),
        ('decimo', 'Décimo'),
        ('once', 'Once'),
]

ELEGIR_IDIOMA = [
        ('es', 'Español'),
        ('en', 'Inglés') 
]

class Genero(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Género")
    slug = models.SlugField(unique=True, help_text="Versión amigable para URL, se genera automáticamente.")

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

class Autor(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Autor")
    biografia = models.TextField(blank=True, verbose_name="Biografía")

    def __str__(self):
        return self.nombre


class Documento(models.Model):
    idioma = models.CharField(max_length=2, choices=ELEGIR_IDIOMA, default='es')
    titulo = models.CharField(max_length=200)
    grado = models.CharField(max_length=10, choices=ELEGIR_GRADO)
    descripcion = CKEditor5Field(config_name='default', blank=True)
    adjunto = models.FileField(upload_to=ruta_de_subida, blank=True, null=True)
    imagen = models.ImageField(upload_to=ruta_imagenes, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)

    autor_principal = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos', verbose_name="Autor de la Obra")
    generos = models.ManyToManyField(Genero, blank=True, related_name='documentos', verbose_name="Géneros")
    
    NIVEL_DIFICULTAD = [
        ('facil', 'Fácil'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    nivel_dificultad = models.CharField(max_length=15, choices=NIVEL_DIFICULTAD, default='intermedio', verbose_name="Nivel de Dificultad")

    @property
    def calificacion_promedio(self):
        # Usamos .aggregate() para obtener el promedio directamente de la BD
        from django.db.models import Avg
        promedio = self.calificaciones.aggregate(Avg('puntuacion'))['puntuacion__avg']
        return round(promedio, 1) if promedio is not None else 0

    @property
    def num_calificaciones(self):
        return self.calificaciones.count()

    def __str__(self):
        return f"({self.get_idioma_display()}) {self.titulo}"
    

class Comentario(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='comentarios')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = CKEditor5Field(config_name='comments', verbose_name="Comentarios")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    adjunto_comentario = models.FileField(upload_to=ruta_subida_comentario, blank=True, null=True)
    imagen_comentario = models.ImageField(upload_to=ruta_imagenes_comentario, blank=True, null=True)

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['fecha_creacion']

    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.documento.titulo}'
    
class Calificacion(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='calificaciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones')
    puntuacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ¡CRÍTICO! Asegura que un usuario solo pueda calificar un documento una vez.
        unique_together = ('documento', 'usuario')
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"

    def __str__(self):
        return f'{self.usuario.username} calificó "{self.documento.titulo}" con {self.puntuacion} estrellas'