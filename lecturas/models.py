from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
        ('septimo', 'Septimo'),
        ('octavo', 'Octavo'),
        ('noveno', 'Noveno'),
        ('decimo', 'Decimo'),
        ('once', 'Once'),
]

ELEGIR_IDIOMA = [
        ('es', 'Español'),
        ('en', 'Inglés') 
]


class Documento(models.Model):
    idioma = models.CharField(max_length=2, choices=ELEGIR_IDIOMA, default='es')
    titulo = models.CharField(max_length=200)
    grado = models.CharField(max_length=10, choices=ELEGIR_GRADO)
    descripcion = models.TextField()
    adjunto = models.FileField(upload_to=ruta_de_subida, blank=True, null=True)
    imagen = models.ImageField(upload_to=ruta_imagenes, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"({self.get_idioma_display()}) {self.titulo}"
    

class Comentario(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField(verbose_name="Comentarios")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    adjunto_comentario = models.FileField(upload_to=ruta_subida_comentario, blank=True, null=True)
    imagen_comentario = models.ImageField(upload_to=ruta_imagenes_comentario, blank=True, null=True)

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['fecha_creacion']

    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.documento.titulo}'