from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

def group_required(group_names):
    """
    Decorador que verifica si un usuario pertenece a al menos uno de los grupos especificados.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
                user_groups = set(g.name for g in request.user.groups.all())
                if user_groups.intersection(set(group_names)):
                    return view_func(request, *args, **kwargs)
            
            raise PermissionDenied
        return wrapper
    return decorator