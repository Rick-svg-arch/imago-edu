from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Clase, Organizacion, PreRegistro, User

from .forms import PreRegistroAdminForm, ProfileAdminForm

# --- GESTIÓN DE ORGANIZACIÓN (Solo para Superusuarios) ---
admin.site.register(Organizacion)

# --- GESTIÓN DE PRE-REGISTRO (Aislado) ---
@admin.register(PreRegistro)
class PreRegistroAdmin(admin.ModelAdmin):
    form = PreRegistroAdminForm
    list_display = ('numero_identificacion', 'organizacion', 'registrado', 'nombres', 'apellidos', 'email')
    list_filter = ('organizacion', 'registrado')
    search_fields = ('numero_identificacion', 'email', 'nombres', 'apellidos')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organizacion=request.user.profile.organizacion)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.organizacion = request.user.profile.organizacion
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'organizacion' in form.base_fields:
                form.base_fields['organizacion'].widget.attrs['disabled'] = True
                form.base_fields['organizacion'].required = False
        return form

# --- GESTIÓN DE CLASES (Aislado) ---
@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'profesor', 'organizacion')
    search_fields = ('nombre', 'profesor__username', 'organizacion__nombre')
    list_filter = ('organizacion',)
    filter_horizontal = ('estudiantes',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organizacion=request.user.profile.organizacion)

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.organizacion = request.user.profile.organizacion
        super().save_model(request, obj, form, change)
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'organizacion']
        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtra el campo 'profesor' de forma inteligente.
        """
        obj_id = request.resolver_match.kwargs.get('object_id')
        
        if db_field.name == "profesor":
            queryset = User.objects.filter(groups__name='Profesor')
            
            if not request.user.is_superuser:
                kwargs["queryset"] = queryset.filter(
                    profile__organizacion=request.user.profile.organizacion
                )
            elif request.user.is_superuser and obj_id:
                try:
                    clase = self.get_object(request, obj_id)
                    kwargs["queryset"] = queryset.filter(
                        profile__organizacion=clase.organizacion
                    )
                except (Clase.DoesNotExist, KeyError):
                    pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        obj_id = request.resolver_match.kwargs.get('object_id')
        
        if db_field.name == "estudiantes":
            queryset = User.objects.filter(groups__name='Estudiante')
            if not request.user.is_superuser:
                kwargs["queryset"] = queryset.filter(
                    profile__organizacion=request.user.profile.organizacion
                )
            elif request.user.is_superuser and obj_id:
                try:
                    clase = self.get_object(request, obj_id)
                    kwargs["queryset"] = queryset.filter(
                        profile__organizacion=clase.organizacion
                    )
                except (Clase.DoesNotExist, KeyError):
                    pass
                    
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# --- GESTIÓN DE PERFILES (Aislado) ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ('user', 'organizacion', 'numero_identificacion', 'user_group')
    search_fields = ('user__username', 'user__email', 'numero_identificacion', 'organizacion__nombre')
    list_filter = ('organizacion', 'user__groups')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organizacion=request.user.profile.organizacion)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Restringe las opciones del campo 'organizacion' para los administradores.
        """
        if not request.user.is_superuser:
            # Verificamos si el campo que se está renderizando es 'organizacion'
            if db_field.name == "organizacion":
                admin_org_pk = request.user.profile.organizacion.pk
                kwargs["queryset"] = Organizacion.objects.filter(pk=admin_org_pk) | \
                                     Organizacion.objects.filter(nombre='Imago')
                                     
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def user_group(self, obj):
        return ' - '.join([t.name for t in obj.user.groups.all().order_by('name')])
    user_group.short_description = 'Grupo'

# --- GESTIÓN DE USUARIOS (Aislado) ---
admin.site.unregister(User) # Desregistramos el UserAdmin por defecto
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(profile__organizacion=request.user.profile.organizacion)