from django.db import models
from django.contrib.auth.models import User

# Create your models here.
def get_default_organization():
    """
    Obtiene la organización 'Imago' o la crea si no existe.
    Devuelve el ID de la organización.
    """
    imago_org, created = Organizacion.objects.get_or_create(nombre='Imago')
    return imago_org.pk

TIPO_IDENTIFICACION = [
    ('TI', 'Tarjeta de Identidad'),
    ('CC', 'Cédula de Ciudadanía'),
    ('CE', 'Cédula de Extranjería'),
    ('PA', 'Pasaporte'),
    ('PPT', 'Permiso por Protección Temporal'),
    ('OT', 'Otro'), 
]

class Organizacion(models.Model):
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de la Organización")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"

    def __str__(self):
        return self.nombre

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Usuario')
    organizacion = models.ForeignKey(
        Organizacion, 
        on_delete=models.CASCADE,
        default=get_default_organization,
        related_name='miembros'
    )
    avatar = models.ImageField(
        default='profiles/default.png', 
        upload_to='users/', 
        null=True, 
        blank=True, 
        verbose_name='Imagen de Perfil'
    )
    adress = models.CharField(max_length=150, null=True, blank=True, verbose_name='Dirección')
    telephone = models.CharField(max_length=150, null=True, blank=True, verbose_name='Teléfono')

    tipo_identificacion = models.CharField(
        max_length=3,
        choices=TIPO_IDENTIFICACION,
        blank=True, null=True,
        verbose_name='Tipo de Identificación'
    )
    numero_identificacion = models.CharField(
        max_length=20,
        unique=True,
        blank=True, null=True,
        db_index=True,
        verbose_name='Número de Identificación'
    )

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['-id']

    def __str__(self):
        return self.user.username


class Clase(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Clase")

    organizacion = models.ForeignKey(
        Organizacion, 
        on_delete=models.CASCADE,
        default=get_default_organization,
        related_name='clases'
    )
    
    profesor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='clases_dirigidas',
        limit_choices_to={'groups__name': 'Profesor'}
    )

    estudiantes = models.ManyToManyField(
        User, 
        related_name='clases_inscritas',
        limit_choices_to={'groups__name': 'Estudiante'}
    )

    class Meta:
        verbose_name = "Clase"
        verbose_name_plural = "Clases"

    def __str__(self):
        return self.nombre
    
class PreRegistro(models.Model):
    organizacion = models.ForeignKey(Organizacion, on_delete=models.CASCADE, related_name='preregistros')
    numero_identificacion = models.CharField(max_length=20, verbose_name="Número de Identificación")
    email = models.EmailField(blank=True, null=True)
    nombre_completo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Completo (Opcional)")
    registrado = models.BooleanField(default=False, verbose_name="¿Ya se registró?")

    ROL_CHOICES = [
        ('Estudiante', 'Estudiante'),
        ('Profesor', 'Profesor'),
        ('Administrativo', 'Administrativo'),
    ]
    rol_asignado = models.CharField(
        max_length=15,
        choices=ROL_CHOICES,
        default='Estudiante',
        verbose_name="Rol Asignado"
    )

    class Meta:
        unique_together = ('organizacion', 'numero_identificacion')
        verbose_name = "Usuario Pre-registrado"
        verbose_name_plural = "Usuarios Pre-registrados"

    def __str__(self):
        return f"{self.numero_identificacion} en {self.organizacion.nombre}"