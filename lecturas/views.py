import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.conf import settings
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied

from .models import Documento, Comentario, ELEGIR_GRADO, ELEGIR_IDIOMA, Calificacion, Autor, Genero
from . import forms
from .decorators import group_required
from .mixins import UserIsAuthorMixin

logger = logging.getLogger(__name__)


def serve_file(request, pk):
    """
    Vista dedicada a servir el archivo adjunto.
    Compatible tanto con almacenamiento local como Cloud Storage.
    """
    documento = get_object_or_404(Documento, pk=pk)
    
    logger.info(f"=== SERVE_FILE para documento {pk} ===")
    logger.info(f"Documento tiene adjunto: {bool(documento.adjunto)}")
    
    if not documento.adjunto:
        logger.warning(f"Documento {pk} no tiene archivo adjunto")
        raise Http404("El documento no tiene un archivo adjunto.")

    logger.info(f"Adjunto name: {documento.adjunto.name}")
    logger.info(f"Adjunto URL: {documento.adjunto.url}")
    logger.info(f"Storage backend: {default_storage.__class__.__name__}")
    logger.info(f"GS_BUCKET_NAME: {getattr(settings, 'GS_BUCKET_NAME', 'NO CONFIGURADO')}")
    
    # Verificar si el archivo existe en storage
    try:
        exists = default_storage.exists(documento.adjunto.name)
        logger.info(f"Archivo existe en storage: {exists}")
    except Exception as e:
        logger.error(f"Error verificando existencia: {e}")
    
    # Determinar el tipo de contenido basado en la extensión
    file_name = documento.adjunto.name
    ext = os.path.splitext(file_name)[1].lower()
    
    content_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain; charset=utf-8',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.epub': 'application/epub+zip',
    }
    
    content_type = content_types.get(ext, 'application/octet-stream')
    
    # Si estamos usando Cloud Storage, redirigir a la URL pública
    if hasattr(settings, 'GS_BUCKET_NAME') and settings.GS_BUCKET_NAME:
        logger.info(f"Redirigiendo a URL de Cloud Storage: {documento.adjunto.url}")
        return redirect(documento.adjunto.url)
    
    # Para almacenamiento local (desarrollo)
    try:
        file_path = documento.adjunto.path
        logger.info(f"Intentando servir desde path local: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado en: {file_path}")
            raise Http404("El archivo no fue encontrado en el servidor.")
        
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type=content_type)
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_name)}"'
            logger.info("Archivo servido exitosamente desde almacenamiento local")
            return response
            
    except (ValueError, NotImplementedError, AttributeError) as e:
        logger.warning(f"No se puede acceder a .path: {e}. Redirigiendo a URL")
        return redirect(documento.adjunto.url)


class DocumentoListView(ListView):
    model = Documento
    template_name = 'lecturas/lista_documentos.html'
    context_object_name = 'documentos'
    ordering = ['-date']
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if 'idioma' in self.kwargs:
            queryset = queryset.filter(idioma=self.kwargs['idioma'])
        if 'grado' in self.kwargs:
            queryset = queryset.filter(grado=self.kwargs['grado'])
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lista_idiomas'] = ELEGIR_IDIOMA
        context['lista_grados'] = ELEGIR_GRADO
        context['current_idioma'] = self.kwargs.get('idioma')
        context['current_grado'] = self.kwargs.get('grado')
        return context


class DocumentoDetailView(DetailView):
    model = Documento
    template_name = 'lecturas/detalle_documento.html'
    context_object_name = 'documento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Log info del documento
        doc = self.get_object()
        user_rating = None
        if self.request.user.is_authenticated:
            try:
                # Buscamos si existe una calificación de este usuario para este documento
                user_rating_obj = Calificacion.objects.get(documento=doc, usuario=self.request.user)
                user_rating = user_rating_obj.puntuacion
            except Calificacion.DoesNotExist:
                user_rating = None # El usuario aún no ha calificado

        context['user_rating'] = user_rating
        logger.info(f"=== DETALLE DOCUMENTO {doc.pk} ===")
        logger.info(f"Tiene adjunto: {bool(doc.adjunto)}")
        if doc.adjunto:
            logger.info(f"Adjunto name: {doc.adjunto.name}")
            logger.info(f"Adjunto URL: {doc.adjunto.url}")
        
        comentarios_list = doc.comentarios.filter(parent__isnull=True).order_by('-fecha_creacion')
        paginator = Paginator(comentarios_list, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['comentarios_page'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['page_obj'] = page_obj
        context['comentario_form'] = forms.ComentarioForm()
        return context


@login_required
@group_required(['Profesor', 'Administrativo'])
def subir_documento(request):
    if request.method == 'POST':
        logger.info("=== SUBIENDO DOCUMENTO ===")
        logger.info(f"POST data: {request.POST}")
        logger.info(f"FILES: {request.FILES.keys()}")
        
        form = forms.DocumentoForm(request.POST, request.FILES)
        
        if form.is_valid():
            logger.info("Formulario válido, guardando...")
            nuevo_documento = form.save(commit=False)
            nuevo_documento.author = request.user
            nuevo_documento.save()
            
            # Los géneros ya se manejan en el método save() del formulario
            form.save_m2m()
            
            logger.info(f"Documento guardado: {nuevo_documento.pk}")
            logger.info(f"Autor: {nuevo_documento.autor_principal}")
            logger.info(f"Géneros: {list(nuevo_documento.generos.all())}")
            
            return redirect('lecturas:detalle_documento', pk=nuevo_documento.pk)
        else:
            logger.error(f"Formulario inválido: {form.errors}")
    else:
        form = forms.DocumentoForm()
    
    # Pasar autores y géneros existentes para el autocompletado
    context = {
        'form': form,
        'autores_existentes': Autor.objects.all().order_by('nombre'),
        'generos_existentes': Genero.objects.all().order_by('nombre')
    }
    
    return render(request, 'lecturas/documento_form.html', context)


class DocumentoUpdateView(LoginRequiredMixin, UserIsAuthorMixin, UpdateView):
    model = Documento
    form_class = forms.DocumentoForm
    template_name = 'lecturas/documento_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar autores y géneros para el autocompletado
        context['autores_existentes'] = Autor.objects.all().order_by('nombre')
        context['generos_existentes'] = Genero.objects.all().order_by('nombre')
        return context
    
    def get_success_url(self):
        return reverse_lazy('lecturas:detalle_documento', kwargs={'pk': self.object.pk})
    

class DocumentoDeleteView(LoginRequiredMixin, UserIsAuthorMixin, DeleteView):
    model = Documento
    template_name = 'lecturas/documento_confirm_delete.html' 
    success_url = reverse_lazy('lecturas:lista_documentos_base')

@login_required
def anadir_comentario(request, pk):
    documento = get_object_or_404(Documento, pk=pk)
    
    if request.method == 'POST':
        form = forms.ComentarioForm(request.POST, request.FILES)
        
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.documento = documento
            comentario.autor = request.user
            comentario.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Para respuestas, contar los hijos actualizados
                new_count = None
                if comentario.parent:
                    new_count = comentario.parent.hijos.count()
                
                html = render_to_string('lecturas/_comentario_item.html', {
                    'comentario': comentario,
                    'user': request.user,
                }, request=request)
                
                return JsonResponse({
                    'success': True,
                    'html': html,
                    'is_nested': comentario.parent is not None,
                    'parent_id': comentario.parent.pk if comentario.parent else None,
                    'new_count': new_count
                })
            
            return redirect('lecturas:detalle_documento', pk=documento.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'errors': form.errors
                }, status=400)

    return redirect('lecturas:detalle_documento', pk=documento.pk)


@login_required
def editar_comentario_ajax(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)
    
    # Comprobación de permisos
    if not (request.user == comentario.autor or 
            request.user.is_superuser or 
            request.user.groups.filter(name='Administrativo').exists()):
        logger.warning(f"Usuario {request.user.username} intentó editar comentario {pk} sin permisos")
        return JsonResponse({'success': False, 'error': 'Permiso denegado'}, status=403)

    if request.method == 'POST':
        logger.info(f"Editando comentario {pk}")
        logger.info(f"POST data keys: {request.POST.keys()}")
        logger.info(f"FILES data keys: {request.FILES.keys()}")
        
        form = forms.ComentarioForm(request.POST, request.FILES, instance=comentario)
        
        if form.is_valid():
            logger.info("Formulario válido, guardando cambios")
            comentario = form.save()
            
            # Renderizar el contenido actualizado del comentario
            html = render_to_string(
                'lecturas/_comentario_contenido.html', 
                {
                    'comentario': comentario, 
                    'user': request.user
                },
                request=request
            )
            
            logger.info("Comentario editado exitosamente")
            return JsonResponse({'success': True, 'html': html})
        else:
            # El formulario tiene errores
            logger.error(f"Errores en formulario: {form.errors}")
            
            # Renderizar el formulario con errores
            form_html = render_to_string(
                'lecturas/_comentario_edit_form.html', 
                {
                    'form': form, 
                    'comentario': comentario
                }, 
                request=request
            )
            
            return JsonResponse({
                'success': False, 
                'form_html': form_html,
                'errors': form.errors
            }, status=400)
    else:
        # Petición GET: devolver el formulario de edición
        logger.info(f"Cargando formulario de edición para comentario {pk}")
        form = forms.ComentarioForm(instance=comentario)
        
        form_html = render_to_string(
            'lecturas/_comentario_edit_form.html', 
            {
                'form': form, 
                'comentario': comentario
            }, 
            request=request
        )
        
        return JsonResponse({'html': form_html})

@login_required
def borrar_comentario_ajax(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)

    # Comprobación de permisos
    if not (request.user == comentario.autor or 
            request.user.is_superuser or 
            request.user.groups.filter(name='Administrativo').exists()):
        logger.warning(f"Usuario {request.user.username} intentó borrar comentario {pk} sin permisos")
        return JsonResponse({'success': False, 'error': 'Permiso denegado'}, status=403)

    if request.method == 'POST':
        logger.info(f"Borrando comentario {pk}")
        comentario.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def calificar_documento_ajax(request, pk):
    if request.method == 'POST':
        documento = get_object_or_404(Documento, pk=pk)
        
        try:
            puntuacion = int(request.POST.get('puntuacion'))
            if not 1 <= puntuacion <= 5:
                raise ValueError("Puntuación fuera de rango")
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Puntuación inválida'}, status=400)

        # Usamos update_or_create para crear o actualizar la calificación en una sola operación
        calificacion, created = Calificacion.objects.update_or_create(
            documento=documento,
            usuario=request.user,
            defaults={'puntuacion': puntuacion}
        )
        
        # Devolvemos los nuevos datos para actualizar la UI
        return JsonResponse({
            'success': True,
            'nuevo_promedio': documento.calificacion_promedio,
            'num_calificaciones': documento.num_calificaciones
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)