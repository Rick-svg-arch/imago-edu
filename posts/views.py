import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q

from .models import Categoria, Tema, Respuesta
from .forms import TemaForm, RespuestaForm, CategoriaForm, RespuestaEditForm
from users.mixins import GroupRequiredMixin
from .mixins import UserIsAuthorMixin

def lista_categorias(request):
    """Muestra la lista de todos los subforos, con búsqueda y paginación."""
    categorias_list = Categoria.objects.all().order_by('nombre')

    query = request.GET.get('q')
    if query:
        categorias_list = categorias_list.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        ).distinct()

    paginator = Paginator(categorias_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'posts/lista_categorias.html', {
        'categorias_page': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    })

def lista_temas(request, slug_categoria):
    """Muestra los temas dentro de una categoría específica y maneja la búsqueda."""
    categoria = get_object_or_404(Categoria, slug=slug_categoria)
    # Empezamos con la lista de temas de la categoría
    temas_list = Tema.objects.filter(categoria=categoria).order_by('-fecha_creacion')

    query = request.GET.get('q')
    if query:
        temas_list = temas_list.filter(
            Q(titulo__icontains=query) |
            Q(autor__username__icontains=query)
        ).distinct()
    paginator = Paginator(temas_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'posts/lista_temas.html', {
        'categoria': categoria, 
        'temas_page': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    })

def detalle_tema(request, pk):
    """
    Muestra un tema, sus respuestas, y maneja la creación de nuevas respuestas.
    """
    tema = get_object_or_404(Tema, pk=pk)
    respuestas_list = Respuesta.objects.filter(tema=tema, parent__isnull=True).order_by('-fecha_creacion')
    
    paginator = Paginator(respuestas_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('users:login')
            
        respuesta_form = RespuestaForm(request.POST, request.FILES)
        if respuesta_form.is_valid():
            nueva_respuesta = respuesta_form.save(commit=False)
            nueva_respuesta.tema = tema
            nueva_respuesta.autor = request.user
            nueva_respuesta.save()
            
            # Para respuestas AJAX, devolvemos información para actualizar la UI
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Renderizar la nueva respuesta como HTML
                html_content = render_to_string('posts/_respuesta_tree.html', {
                    'respuesta': nueva_respuesta,
                    'respuesta_form': RespuestaForm(),
                    'user': request.user,
                    'depth': 0
                }, request=request)
                
                return JsonResponse({
                    'success': True,
                    'html': html_content,
                    'respuesta_id': nueva_respuesta.pk,
                    'is_nested': nueva_respuesta.parent is not None,
                    'parent_id': nueva_respuesta.parent.pk if nueva_respuesta.parent else None
                })
            
            # Redirección normal para no-AJAX
            current_page = request.POST.get('current_page') or request.GET.get('page') or '1'
            url_base = reverse('posts:detalle_tema', kwargs={'pk': tema.pk})
            
            if current_page and current_page != '1':
                url_con_pagina = f'{url_base}?page={current_page}'
            else:
                url_con_pagina = url_base
                
            url_final = f'{url_con_pagina}#respuesta-{nueva_respuesta.pk}'
            return redirect(url_final)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                error_message = next(iter(respuesta_form.errors.values()))[0]
                return JsonResponse({'success': False, 'error': error_message}, status=400)
    
    else:
        respuesta_form = RespuestaForm()

    return render(request, 'posts/detalle_tema.html', {
        'tema': tema,
        'respuestas_page': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'respuesta_form': respuesta_form
    })

@login_required(login_url="/users/login/")
def crear_tema(request, slug_categoria):
    """Crea un nuevo tema dentro de una categoría."""
    categoria = get_object_or_404(Categoria, slug=slug_categoria)
    if request.method == 'POST':
        form = TemaForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo_tema = form.save(commit=False)
            nuevo_tema.categoria = categoria
            nuevo_tema.autor = request.user
            nuevo_tema.save()
            return redirect('posts:detalle_tema', pk=nuevo_tema.pk) # Redirigir al nuevo tema
    else:
        form = TemaForm()
    return render(request, 'posts/form_tema.html', {'form': form, 'categoria': categoria})

class CategoriaCreateView(GroupRequiredMixin, CreateView):
    groups_required = ['Administrativo', 'Profesor']
    model = Categoria
    form_class = CategoriaForm
    template_name = 'posts/crear_categoria.html'
    success_url = reverse_lazy('posts:lista_categorias')

    def form_valid(self, form):
        """
        Sobrescribimos este método para generar el slug automáticamente
        a partir del nombre de la categoría antes de guardarla.
        """
        form.instance.autor = self.request.user 
        form.instance.slug = slugify(form.cleaned_data['nombre'])
        
        return super().form_valid(form)    
class TemaUpdateView(LoginRequiredMixin, UserIsAuthorMixin, UpdateView):
    model = Tema
    form_class = TemaForm
    template_name = 'posts/form_tema.html'

    def get_success_url(self):
        return reverse_lazy('posts:detalle_tema', kwargs={'pk': self.object.pk})

class TemaDeleteView(LoginRequiredMixin, UserIsAuthorMixin, DeleteView):
    model = Tema
    template_name = 'posts/confirm_delete_tema.html'
    success_url = reverse_lazy('posts:lista_categorias')


@login_required
def editar_respuesta_ajax(request, pk):
    respuesta = get_object_or_404(Respuesta, pk=pk)

    # Comprobación de permisos manual
    is_author = request.user == respuesta.autor
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrativo').exists()
    if not is_author and not is_admin:
        return HttpResponseForbidden("No tienes permiso para editar esta respuesta.")

    if request.method == 'POST':
        form = RespuestaEditForm(request.POST, request.FILES, instance=respuesta)
        if form.is_valid():
            form.save()
            # Devolvemos la respuesta actualizada y re-renderizada
            html = render_to_string('posts/_respuesta_tree.html', {
                'respuesta': respuesta,
                'respuesta_form': RespuestaForm(), # Un form limpio para anidar
                'user': request.user
            }, request=request)
            return JsonResponse({'success': True, 'html': html})
        else:
            error_message = next(iter(form.errors.values()))[0]
            return JsonResponse({'success': False, 'error': error_message}, status=400)
    else:
        # Petición GET: devolver el formulario de edición
        form = RespuestaEditForm(instance=respuesta)
        form_html = render_to_string('posts/_form_respuesta_ajax.html', {
            'form': form,
            'respuesta': respuesta
        }, request=request)
        return JsonResponse({'html': form_html})

@login_required
def borrar_respuesta_ajax(request, pk):
    respuesta = get_object_or_404(Respuesta, pk=pk)

    # Comprobación de permisos manual
    is_author = request.user == respuesta.autor
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrativo').exists()
    if not is_author and not is_admin:
        return HttpResponseForbidden("No tienes permiso para borrar esta respuesta.")

    if request.method == 'POST':
        respuesta.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
def get_hijos_respuesta_ajax(request, pk_parent):
    # Obtenemos la respuesta "padre"
    parent_respuesta = get_object_or_404(Respuesta, pk=pk_parent)
    
    # Obtenemos todos sus hijos directos
    hijos = parent_respuesta.hijos.all()
    
    # Preparamos el contexto para la plantilla parcial
    context = {
        'respuestas': hijos,
        'respuesta_form': RespuestaForm(), # Para los formularios de respuesta anidados
        'user': request.user
    }
    
    # Renderizamos el HTML de los hijos usando una plantilla parcial
    html = render_to_string('posts/_hijos_list.html', context, request=request)
    
    # Devolvemos el HTML como una respuesta JSON
    return JsonResponse({'html': html})

@login_required
def guardar_tema_ajax(request, pk):
    """ Vista AJAX para el autoguardado de los campos de texto de un Tema. """
    # --- CORRECCIÓN DE PERMISOS ---
    # Obtenemos el objeto y LUEGO verificamos el permiso manualmente.
    tema = get_object_or_404(Tema, pk=pk)
    if tema.autor != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para editar este tema.")
    # --- FIN CORRECCIÓN ---

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            for field_name, value in data.items():
                if hasattr(tema, field_name):
                    setattr(tema, field_name, value)
            
            tema.save(update_fields=data.keys())
            return JsonResponse({'success': True, 'message': 'Cambios guardados.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


@login_required
def subir_banner_ajax(request, pk):
    """ Vista AJAX dedicada a la subida del banner de un Tema. """
    # --- CORRECCIÓN DE PERMISOS ---
    tema = get_object_or_404(Tema, pk=pk)
    if tema.autor != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para editar este tema.")
    # --- FIN CORRECCIÓN ---

    if request.method == 'POST':
        file = request.FILES.get('banner')
        if not file:
            return JsonResponse({'success': False, 'error': 'No se encontró ningún archivo.'}, status=400)
        
        form = TemaForm({'titulo': tema.titulo}, {'banner': file}, instance=tema)
        if form.is_valid():
            tema.banner = form.cleaned_data['banner']
            tema.save(update_fields=['banner'])
            return JsonResponse({'success': True, 'file_url': tema.banner.url})
        else:
            return JsonResponse({'success': False, 'error': form.errors.get('banner', ['Error de validación.'])[0]}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)