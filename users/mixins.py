from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin


class GroupRequiredMixin(AccessMixin):
    """
    Mixin que verifica que el usuario pertenece a uno de los grupos requeridos.
    """
    groups_required = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        user_groups = set(g.name for g in request.user.groups.all())
        
        if not user_groups.intersection(set(self.groups_required)) and not request.user.is_superuser:
            raise PermissionDenied("No tienes permiso para acceder a esta página.")
            
        return super().dispatch(request, *args, **kwargs)