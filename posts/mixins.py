from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

class UserIsAuthorMixin(AccessMixin):
    """
    Verifica que el usuario logueado es el autor del objeto,
    un superusuario, o un Administrativo.
    """
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        
        is_author = obj.autor == request.user
        is_superuser = request.user.is_superuser
        is_administrativo = request.user.groups.filter(name='Administrativo').exists()

        if not is_author and not is_superuser and not is_administrativo:
            raise PermissionDenied("No tienes permiso para realizar esta acción.")
        
        return super().dispatch(request, *args, **kwargs)