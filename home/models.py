from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class HeroConfiguration(models.Model):
    titulo = models.CharField(max_length=150, help_text="El texto principal y más grande del Hero.")
    subtitulo = models.TextField(max_length=300, blank=True, help_text="Un texto secundario que aparece debajo del título.")
    texto_boton = models.CharField(max_length=50, blank=True, verbose_name="Texto del Botón")
    enlace_boton = models.CharField(max_length=255, blank=True, verbose_name="URL del Botón", help_text="Ejemplo: /lecturas/")
    imagen_fondo = models.ImageField(upload_to='hero/backgrounds/', verbose_name="Imagen de Fondo")

    class Meta:
        verbose_name = "1. Configuración de la Sección Hero"
        verbose_name_plural = "1. Configuración de la Sección Hero"

    def __str__(self):
        return "Configuración de la Sección Hero Principal"

class HomePageBlock(models.Model):
    class BlockType(models.TextChoices):
        REFLEXION = 'reflexion', 'Reflexión (Texto simple con título)'
        TEXTO_CON_FONDO = 'texto_fondo', 'Texto con Imagen de Fondo (Estática)'
        PARALLAX = 'parallax', 'Sección con Efecto Parallax'
        # Puedes añadir más tipos de bloques aquí en el futuro
        MEJOR_VALORADAS = 'seccion_valoradas', 'Sección: Lecturas Mejor Valoradas'
        RECIENTES = 'seccion_recientes', 'Sección: Novedades'
        FOROS_DESTACADOS = 'seccion_foros', 'Sección: Foros Más Activos'

    class ContentPosition(models.TextChoices):
        LEFT = 'left', 'Izquierda'
        CENTER = 'center', 'Centro'
        RIGHT = 'right', 'Derecha'

    class ButtonStyle(models.TextChoices):
        PRIMARY = 'primary', 'Primario (Relleno)'
        SECONDARY = 'secondary', 'Secundario (Borde)'

    tipo_bloque = models.CharField(
        max_length=30,
        choices=BlockType.choices,
        default=BlockType.REFLEXION,
        verbose_name="Tipo de Bloque",
        help_text="Elige el diseño visual para este bloque de contenido."
    )
    
    titulo = models.CharField(
        max_length=200,
        blank=True,
        help_text="El título principal del bloque."
    )

    contenido = CKEditor5Field(
        'Contenido', 
        config_name='default',
        blank=True,
        help_text="El cuerpo principal del bloque. No es necesario para los bloques de 'Sección'."
    )
    
    imagen_fondo = models.ImageField(
        upload_to='home_blocks/backgrounds/',
        blank=True,
        null=True,
        verbose_name="Imagen de Fondo",
        help_text="Sube una imagen de fondo (solo para el tipo 'Texto con Imagen de Fondo')."
    )

    posicion_contenido = models.CharField(
        max_length=10,
        choices=ContentPosition.choices,
        default=ContentPosition.CENTER,
        verbose_name="Posición del Contenido",
        help_text="Elige dónde aparecerá el texto."
    )

    enlace_texto_1 = models.CharField(max_length=50, blank=True, verbose_name="Texto del Botón 1")
    enlace_url_1 = models.CharField(max_length=255, blank=True, verbose_name="URL del Botón 1")
    enlace_estilo_1 = models.CharField(max_length=10, choices=ButtonStyle.choices, default=ButtonStyle.PRIMARY, verbose_name="Estilo del Botón 1")
    enlace_nueva_pestana_1 = models.BooleanField(default=False, verbose_name="¿Abrir en pestaña nueva?")
    
    enlace_texto_2 = models.CharField(max_length=50, blank=True, verbose_name="Texto del Botón 2")
    enlace_url_2 = models.CharField(max_length=255, blank=True, verbose_name="URL del Botón 2")
    enlace_estilo_2 = models.CharField(max_length=10, choices=ButtonStyle.choices, default=ButtonStyle.SECONDARY, verbose_name="Estilo del Botón 2")
    enlace_nueva_pestana_2 = models.BooleanField(default=False, verbose_name="¿Abrir en pestaña nueva?")

    activo = models.BooleanField(
        default=True,
        verbose_name="Bloque Activo",
        help_text="Desmarca esta casilla para ocultar el bloque de la página de inicio sin borrarlo."
    )

    orden = models.PositiveIntegerField(
        default=0,
        editable=False,
        db_index=True
    )

    class Meta:
        verbose_name = "2. Bloque de la Página de Inicio"
        verbose_name_plural = "2. Bloques de la Página de Inicio"
        ordering = ['orden']

    def __str__(self):
        if self.titulo:
            return f"{self.get_tipo_bloque_display()} - {self.titulo}"
        return self.get_tipo_bloque_display()