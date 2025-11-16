from django.contrib.auth.models import Group, User
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Profile

@receiver(post_save, sender=User)
def create_profile_and_groups(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de crear o actualizar un usuario.
    - Crea el perfil si no existe
    - Crea los grupos necesarios si no existen
    - Asigna automáticamente el grupo 'Administrativo' a los superusuarios
    """
    if created:
        # Crear el perfil si es un usuario nuevo
        Profile.objects.get_or_create(user=instance)

        # Asegurarse de que los grupos existan
        Group.objects.get_or_create(name='Estudiante')
        Group.objects.get_or_create(name='Profesor')
        Group.objects.get_or_create(name='Administrativo')

        # Si es un superusuario, asignarlo automáticamente al grupo Administrativo
        if instance.is_superuser:
            admin_group, _ = Group.objects.get_or_create(name='Administrativo')
            instance.groups.add(admin_group)
    else:
        # Si se actualiza un usuario existente y se convierte en superusuario
        if instance.is_superuser:
            admin_group, _ = Group.objects.get_or_create(name='Administrativo')
            # Agregar al grupo solo si no está ya
            if admin_group not in instance.groups.all():
                instance.groups.add(admin_group)