import csv
import io
import re
import json
import chardet
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView, UpdateView, CreateView, DetailView, DeleteView
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Profile, Clase, PreRegistro
from .mixins import GroupRequiredMixin
from . import forms

# Create your views here.

def process_student_ids(clase, ids_texto):
    """Función de ayuda para no repetir código."""
    if ids_texto:
        ids_limpios = [id.strip() for id in re.split(r'[,\s\n]+', ids_texto) if id.strip()]
        perfiles = Profile.objects.filter(
            numero_identificacion__in=ids_limpios,
            organizacion=clase.organizacion
        )
        usuarios_a_anadir = [perfil.user for perfil in perfiles]
        clase.estudiantes.add(*usuarios_a_anadir)

def register_view(request):
    if request.method == "POST":
        form = forms.CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Llama a tu método save() personalizado
            login(request, user)
            
            next_url = request.POST.get('next', '/')
            if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
                next_url = '/'
            return redirect(next_url)
    else:
        form = forms.CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            next_url = request.POST.get('next', '/')
            if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
                next_url = '/'
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    if request.method == "POST":
        logout(request)
        next_url = request.GET.get('next', '/')
        if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
            next_url = '/'
        return redirect(next_url)
    return redirect('/')

def get_users_from_ids(id_list, organizacion):
    """
    Función de ayuda para buscar usuarios por ID dentro de una organización.
    Devuelve un conjunto (set) de objetos User.
    """
    if not id_list:
        return set()
    
    perfiles = Profile.objects.filter(
        numero_identificacion__in=id_list,
        organizacion=organizacion
    )
    return {perfil.user for perfil in perfiles}

class UserListView(GroupRequiredMixin, ListView):
    groups_required = ['Administrativo', 'Profesor']
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        """
        Sobrescribimos el queryset para mostrar SOLO usuarios de la misma organización.
        """
        # Obtenemos la organización del usuario que está haciendo la petición
        organizacion_actual = self.request.user.profile.organizacion

        # El queryset base ahora filtra por organización
        queryset = User.objects.filter(
            profile__organizacion=organizacion_actual
        ).exclude(pk=self.request.user.pk).order_by('username')
        
        query = self.request.GET.get('q')
        
        if query:
            queryset = queryset.filter(
                Q(profile__numero_identificacion__icontains=query) |
                Q(username__icontains=query) |
                Q(email__icontains=query)
            ).distinct()
            
        return queryset


class UserGroupUpdateView(GroupRequiredMixin, View):
    groups_required = ['Administrativo']
    template_name = 'users/user_group_form.html'

    def get(self, request, pk):
        organizacion_actual = request.user.profile.organizacion
        # Solo se puede obtener el usuario si su 'pk' y su organización coinciden.
        user_to_edit = get_object_or_404(User, pk=pk, profile__organizacion=organizacion_actual)
        
        form = forms.UserGroupForm(initial={'groups': user_to_edit.groups.all()})
        return render(request, self.template_name, {'form': form, 'user_to_edit': user_to_edit})

    def post(self, request, pk):
        organizacion_actual = request.user.profile.organizacion
        user_to_edit = get_object_or_404(User, pk=pk, profile__organizacion=organizacion_actual)
        
        form = forms.UserGroupForm(request.POST)
        if form.is_valid():
            selected_groups = form.cleaned_data['groups']
            user_to_edit.groups.set(selected_groups)
            return redirect('users:manage_users_list')

        return render(request, self.template_name, {'form': form, 'user_to_edit': user_to_edit})
    

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_organization = user.profile.organizacion if hasattr(user, 'profile') else None

        if hasattr(user, 'profile'):
            context['profile'] = user.profile
        else:
            context['profile'] = Profile.objects.create(user=user)

        if user.groups.filter(name='Profesor').exists() and user_organization:
            context['clases_dirigidas'] = Clase.objects.filter(profesor=user, organizacion=user_organization).prefetch_related('estudiantes')

        # Datos para Administrativo
        if user.groups.filter(name='Administrativo').exists() and user_organization:
            context['todas_las_clases'] = Clase.objects.filter(organizacion=user_organization)
            context['todos_los_usuarios'] = User.objects.filter(
                profile__organizacion=user_organization
            ).exclude(is_superuser=True)  
        return context
    

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.ProfileUpdateForm
    template_name = 'users/profile_form.html'
    success_url = reverse_lazy('users:dashboard')

    def get_object(self, queryset=None):
        # El objeto a editar es el propio usuario logueado
        return self.request.user

class ClassCreateView(GroupRequiredMixin, CreateView):
    groups_required = ['Profesor', 'Administrativo']
    model = Clase
    template_name = 'users/class_form.html'
    success_url = reverse_lazy('users:dashboard')

    def get_form_class(self):
        if self.request.user.groups.filter(name='Administrativo').exists():
            return forms.ClassFormForAdmin
        return forms.ClassFormForProfessor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organizacion'] = self.request.user.profile.organizacion
        return kwargs

    def form_valid(self, form):
        # Asigna la organización y el profesor
        form.instance.organizacion = self.request.user.profile.organizacion
        if not self.request.user.groups.filter(name='Administrativo').exists():
            form.instance.profesor = self.request.user
        
        response = super().form_valid(form)
        clase = self.object

        # Recogemos estudiantes del selector y del texto
        estudiantes_finales = set(form.cleaned_data.get('estudiantes', []))
        ids_texto = form.cleaned_data.get('estudiantes_por_id', '')
        if ids_texto:
            usuarios_por_texto = get_users_from_ids(re.split(r'[,\s\n]+', ids_texto), clase.organizacion)
            estudiantes_finales.update(usuarios_por_texto)
        
        if estudiantes_finales:
            clase.estudiantes.set(estudiantes_finales)
        
        return response

class ClassUpdateView(GroupRequiredMixin, UpdateView):
    groups_required = ['Profesor', 'Administrativo']
    model = Clase
    template_name = 'users/class_form.html'
    success_url = reverse_lazy('users:dashboard')

    def get_form_class(self):
        if self.request.user.groups.filter(name='Administrativo').exists():
            return forms.ClassFormForAdmin
        return forms.ClassFormForProfessor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organizacion'] = self.get_object().organizacion
        return kwargs

    def form_valid(self, form):
        clase = form.save()

        estudiantes_finales = set(form.cleaned_data.get('estudiantes', []))
        ids_texto = form.cleaned_data.get('estudiantes_por_id', '')
        if ids_texto:
            usuarios_por_texto = get_users_from_ids(re.split(r'[,\s\n]+', ids_texto), clase.organizacion)
            estudiantes_finales.update(usuarios_por_texto)
        
        # Usamos set() para actualizar la lista de estudiantes
        clase.estudiantes.set(estudiantes_finales)
        
        return redirect(self.get_success_url())
    

class ClaseDetailView(LoginRequiredMixin, DetailView):
    model = Clase
    template_name = 'users/clase_detail.html'
    context_object_name = 'clase'

    def get_object(self, queryset=None):
        """
        Sobrescribimos este método para añadir una capa de seguridad.
        Un usuario solo puede ver la clase si es el profesor, un estudiante inscrito,
        un administrativo o un superusuario.
        """
        clase = super().get_object(queryset)
        user = self.request.user
        
        es_profesor = clase.profesor == user
        es_estudiante = user in clase.estudiantes.all()
        es_admin = user.groups.filter(name='Administrativo').exists()
        
        if es_profesor or es_estudiante or es_admin or user.is_superuser:
            return clase
        else:
            # Si no cumple ninguna condición, no tiene permiso para verla.
            raise PermissionDenied("No tienes acceso a los detalles de esta clase.")
        

class PasswordResetByAdminView(GroupRequiredMixin, View):
    groups_required = ['Administrativo']

    def post(self, request, pk):
        user_to_reset = get_object_or_404(User, pk=pk)
        
        # Le pasamos el email del usuario para que sepa a dónde enviar el enlace.
        form = PasswordResetForm({'email': user_to_reset.email})
        
        if form.is_valid():
            form.save(
                request=request,
                from_email='noreply@imago.edu.com', #Cambia esto por tu correo
                email_template_name='registration/password_reset_email.html' # Plantilla del correo
            )
            messages.success(request, f'Se ha enviado un correo para restablecer la contraseña a {user_to_reset.email}.')
        else:
            messages.error(request, 'No se pudo iniciar el restablecimiento de contraseña. Asegúrate de que el usuario tenga un email válido.')
            
        return redirect('users:manage_users_list')
    
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    Vista para que un usuario logueado cambie su propia contraseña.
    """
    template_name = 'users/change_password_form.html'
    success_url = reverse_lazy('users:password_change_done')

class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """
    Página que se muestra después de que el cambio de contraseña ha sido exitoso.
    """
    template_name = 'users/change_password_done.html'


class FindStudentsByIdView(GroupRequiredMixin, View):
    groups_required = ['Profesor', 'Administrativo']

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            ids_texto = data.get('ids', '')
            organizacion_pk = data.get('organizacion_pk')

            if not ids_texto or not organizacion_pk:
                return JsonResponse({'error': 'Faltan datos.'}, status=400)

            ids_limpios = [id.strip() for id in re.split(r'[,\s\n]+', ids_texto) if id.strip()]
            
            perfiles_encontrados = Profile.objects.filter(
                numero_identificacion__in=ids_limpios,
                organizacion_id=organizacion_pk
            ).select_related('user').order_by('user__last_name')

            encontrados = []
            ids_encontrados = set()
            for perfil in perfiles_encontrados:
                encontrados.append({
                    'id': perfil.user.pk,
                    'full_name': perfil.user.get_full_name(),
                    'username': perfil.user.username,
                    'numero_id': perfil.numero_identificacion
                })
                ids_encontrados.add(perfil.numero_identificacion)
            
            no_encontrados = [id for id in ids_limpios if id not in ids_encontrados]
            
            return JsonResponse({
                'encontrados': encontrados,
                'no_encontrados': no_encontrados
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        
class PreRegistroManagerView(GroupRequiredMixin, ListView): # Renombramos la vista
    groups_required = ['Administrativo']
    model = PreRegistro
    template_name = 'users/preregistro_manager.html' # Usaremos una nueva plantilla
    context_object_name = 'preregistros'
    paginate_by = 25

    def get_queryset(self):
        # ... (la lógica de get_queryset para filtrar y buscar no cambia) ...
        organizacion_actual = self.request.user.profile.organizacion
        queryset = PreRegistro.objects.filter(organizacion=organizacion_actual).order_by('nombre_completo')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(...) | Q(...))
        return queryset

    def get_context_data(self, **kwargs):
        """Añade los formularios al contexto."""
        context = super().get_context_data(**kwargs)
        # Añadimos instancias vacías de los formularios para el método GET
        if 'manual_form' not in context:
            context['manual_form'] = forms.PreRegistroForm()
        if 'csv_form' not in context:
            context['csv_form'] = forms.CSVImportForm()
        return context

    def post(self, request, *args, **kwargs):
        """Maneja los envíos de los dos formularios."""
        # Necesitamos volver a obtener el queryset y los objetos de la lista
        # para re-renderizar la página en caso de éxito o error.
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        # Determinamos qué formulario se envió
        if 'submit_manual' in request.POST:
            manual_form = forms.PreRegistroForm(request.POST)
            if manual_form.is_valid():
                preregistro = manual_form.save(commit=False)
                preregistro.organizacion = request.user.profile.organizacion
                preregistro.save()
                messages.success(request, f"Usuario '{preregistro.numero_identificacion}' añadido a la whitelist.")
                return redirect('users:manage_preregistros_list')
            else:
                context['manual_form'] = manual_form # Pasa el formulario con errores
        
        elif 'submit_csv' in request.POST:
            csv_form = forms.CSVImportForm(request.POST, request.FILES)
            if csv_form.is_valid():
                success_count, errors = self.process_csv(...)
                context['success_count'] = success_count
                context['errors'] = errors
            else:
                context['csv_form'] = csv_form 

        return self.render_to_response(context)
    
class PreRegistroUpdateView(GroupRequiredMixin, UpdateView):
    groups_required = ['Administrativo']
    model = PreRegistro
    form_class = forms.PreRegistroForm
    template_name = 'users/preregistro_form.html'
    success_url = reverse_lazy('users:manage_preregistros_list')

    def get_queryset(self):
        # Seguridad: un admin solo puede editar pre-registros de su propia organización
        return PreRegistro.objects.filter(organizacion=self.request.user.profile.organizacion)

class PreRegistroDeleteView(GroupRequiredMixin, DeleteView):
    groups_required = ['Administrativo']
    model = PreRegistro
    template_name = 'users/preregistro_confirm_delete.html'
    success_url = reverse_lazy('users:manage_preregistros_list')

    def get_queryset(self):
        # Misma comprobación de seguridad para el borrado
        return PreRegistro.objects.filter(organizacion=self.request.user.profile.organizacion)
    
    
class PreviewStudentsFromCSVView(GroupRequiredMixin, View):
    groups_required = ['Profesor', 'Administrativo']

    def post(self, request, *args, **kwargs):
        try:
            csv_file = request.FILES.get('estudiantes_csv')
            organizacion_pk = request.POST.get('organizacion_pk')
            page_number = request.POST.get('page', 1)

            if not csv_file or not organizacion_pk:
                return JsonResponse({'error': 'Falta el archivo CSV o la organización.'}, status=400)

            raw_data = csv_file.read()
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            data_set = raw_data.decode(encoding)
            io_string = io.StringIO(data_set)
            dialect = csv.Sniffer().sniff(io_string.readline(), delimiters=',;')
            io_string.seek(0)
            reader = csv.DictReader(io_string, dialect=dialect)
            
            ids_from_csv = [re.sub(r'\D', '', row['numero_identificacion']) for row in reader if row.get('numero_identificacion')]

            # Buscamos y paginamos los resultados
            perfiles = Profile.objects.filter(
                numero_identificacion__in=ids_from_csv,
                organizacion_id=organizacion_pk
            ).select_related('user').order_by('user__last_name')
            
            paginator = Paginator(perfiles, 10) # 10 por página
            page_obj = paginator.get_page(page_number)

            encontrados = []
            ids_encontrados = {p.numero_identificacion for p in perfiles}
            for perfil in page_obj.object_list:
                encontrados.append({
                    'id': perfil.user.pk,
                    'full_name': perfil.user.get_full_name() or perfil.user.username,
                    'username': perfil.user.username,
                    'numero_id': perfil.numero_identificacion
                })
            
            no_encontrados = [id for id in ids_from_csv if id not in ids_encontrados]
            
            return JsonResponse({
                'encontrados': encontrados,
                'no_encontrados': no_encontrados,
                'pagination': {
                    'has_next': page_obj.has_next(),
                    'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                }
            })
        except Exception as e:
            return JsonResponse({'error': f"Error al procesar el archivo: {e}"}, status=500)