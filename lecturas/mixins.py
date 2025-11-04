from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

class UserIsAuthorMixin(AccessMixin):
    """
    Mixin para verificar que el usuario logueado es el autor del objeto, administrativo o superusuario.
    """
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        author_field_name = 'author' if hasattr(obj, 'author') else 'autor'
        is_author = getattr(obj, author_field_name) == request.user
        is_superuser = request.user.is_superuser
        is_administrativo = request.user.groups.filter(name='Administrativo').exists()
        
        if not is_author and not is_superuser and not is_administrativo:
            raise PermissionDenied("No tienes permiso para realizar esta acción.")
        
        return super().dispatch(request, *args, **kwargs)