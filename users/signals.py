from django.contrib.auth.models import Group, User
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Profile

@receiver(post_save, sender=User)
def create_profile_and_groups(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

        Group.objects.get_or_create(name='Estudiante')
        Group.objects.get_or_create(name='Profesor')
        Group.objects.get_or_create(name='Administrativo')