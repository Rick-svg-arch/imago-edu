import os
import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseForbidden
from django.db.models import Q
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
    paginate_by = 16
    
    def get_queryset(self):
        # ... (esta función no cambia, la dejamos como está)
        queryset = super().get_queryset()
        if 'idioma' in self.kwargs:
            queryset = queryset.filter(idioma=self.kwargs['idioma'])
        if 'grado' in self.kwargs:
            queryset = queryset.filter(grado=self.kwargs['grado'])
        
        query = self.request.GET.get('q')
        
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) |
                Q(autor_principal__nombre__icontains=query) |
                Q(generos__nombre__icontains=query)
            ).distinct()
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lista_idiomas'] = ELEGIR_IDIOMA
        
        todos_los_grados = dict(ELEGIR_GRADO)
        
        structured_grados = [
            # Separamos 'General' para que aparezca primero y solo.
            {'group_name': None, 'grades': [('general', todos_los_grados.pop('general'))]},
            
            {'group_name': 'Educación Básica', 'grades': [
                ('primero', todos_los_grados.pop('primero')),
                ('segundo', todos_los_grados.pop('segundo')),
                ('tercero', todos_los_grados.pop('tercero')),
                ('cuarto', todos_los_grados.pop('cuarto')),
                ('quinto', todos_los_grados.pop('quinto')),
            ]},
            {'group_name': 'Bachillerato', 'grades': [
                ('sexto', todos_los_grados.pop('sexto')),
                ('septimo', todos_los_grados.pop('septimo')),
                ('octavo', todos_los_grados.pop('octavo')),
                ('noveno', todos_los_grados.pop('noveno')),
                ('decimo', todos_los_grados.pop('decimo')),
                ('once', todos_los_grados.pop('once')),
            ]},
            {'group_name': 'Profesionales', 'grades': [
                ('docentes', todos_los_grados.pop('docentes')),
                ('directivos', todos_los_grados.pop('directivos')),
            ]}
        ]
        
        # Si quedan grados sin agrupar, los añadimos al final.
        if todos_los_grados:
            structured_grados.append({'group_name': 'Otros', 'grades': list(todos_los_grados.items())})

        context['structured_grados'] = structured_grados
        # --- FIN DE LA LÓGICA ---
        
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
                
                # CREAR NUEVO FORMULARIO LIMPIO
                nuevo_form = forms.ComentarioForm()
                
                html = render_to_string('lecturas/_comentario_item.html', {
                    'comentario': comentario,
                    'user': request.user,
                }, request=request)
                
                # Renderizar formulario limpio SOLO para comentarios principales
                clean_form_html = None
                if not comentario.parent:  # Solo para comentarios principales
                    clean_form_html = render_to_string('lecturas/_comentario_form_clean.html', {
                        'comentario_form': nuevo_form,
                        'documento': documento  # ¡IMPORTANTE! Pasar el documento para la URL
                    }, request=request)
                
                return JsonResponse({
                    'success': True,
                    'html': html,
                    'is_nested': comentario.parent is not None,
                    'parent_id': comentario.parent.pk if comentario.parent else None,
                    'new_count': new_count,
                    'clean_form_html': clean_form_html  # Formulario limpio para comentarios principales
                })
            
            return redirect('lecturas:detalle_documento', pk=documento.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                error_message = ". ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
                return JsonResponse({
                    'success': False, 
                    'error': error_message or "Hubo un error al validar los datos."
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
        logger.info(f"=== EDITANDO COMENTARIO {pk} ===")
        logger.info(f"POST data keys: {request.POST.keys()}")
        logger.info(f"FILES data keys: {request.FILES.keys()}")

        form = forms.ComentarioEditForm(request.POST, request.FILES, instance=comentario)
        
        # Depuración detallada de archivos
        for key in request.FILES.keys():
            file = request.FILES[key]
            logger.info(f"Archivo recibido - Campo: {key}, Nombre: {file.name}, Tamaño: {file.size}")
        
        if form.is_valid():
            logger.info("Formulario válido, guardando cambios")
            
            # Guardar el comentario
            comentario_actualizado = form.save(commit=False)
            
            # Log de archivos antes de guardar
            if hasattr(comentario_actualizado, 'adjunto_comentario') and comentario_actualizado.adjunto_comentario:
                logger.info(f"Adjunto a guardar: {comentario_actualizado.adjunto_comentario.name}")
            if hasattr(comentario_actualizado, 'imagen_comentario') and comentario_actualizado.imagen_comentario:
                logger.info(f"Imagen a guardar: {comentario_actualizado.imagen_comentario.name}")
            
            comentario_actualizado.save()
            
            # Verificar después de guardar
            comentario_actualizado.refresh_from_db()
            logger.info(f"Después de guardar - Adjunto: {bool(comentario_actualizado.adjunto_comentario)}, Imagen: {bool(comentario_actualizado.imagen_comentario)}")
            
            # Renderizar el contenido actualizado del comentario
            html = render_to_string(
                'lecturas/_comentario_contenido.html', 
                {
                    'comentario': comentario_actualizado, 
                    'user': request.user
                },
                request=request
            )
            
            logger.info("Comentario editado exitosamente")
            return JsonResponse({'success': True, 'html': html})
        else:
            # El formulario tiene errores
            logger.error(f"Errores en formulario: {form.errors}")
            
            error_message = ". ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
            return JsonResponse({
                'success': False, 
                'error': error_message or "Por favor, corrige los errores."
            }, status=400)
            
    else:
        # Petición GET: devolver el formulario de edición
        logger.info(f"Cargando formulario de edición para comentario {pk}")
        form = forms.ComentarioEditForm(instance=comentario)
        
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

@login_required
def guardar_documento_ajax(request, pk):
    """
    Vista AJAX para el autoguardado de campos del formulario de Documento.
    Ahora maneja la creación de nuevas etiquetas para campos Select2.
    """
    try:
        documento = DocumentoUpdateView().get_queryset().get(pk=pk)
    except Documento.DoesNotExist:
        return HttpResponseForbidden("No tienes permiso para editar este documento o no existe.")
    except Exception as e:
        logger.error(f"Error inesperado al obtener documento {pk} para autoguardado: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor.'}, status=500)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            field_name, value = next(iter(data.items()))

            # --- LÓGICA MEJORADA PARA MANEJAR STRINGS O IDs ---

            if field_name == 'autor_principal':
                # Si el valor no es un número, es un nuevo autor.
                if value and isinstance(value, str) and not value.isdigit():
                    autor, _ = Autor.objects.get_or_create(nombre=value)
                    documento.autor_principal = autor
                elif value:
                    documento.autor_principal_id = value
                else:
                    documento.autor_principal = None
                documento.save(update_fields=['autor_principal'])

            elif field_name == 'generos':
                final_pks = []
                if isinstance(value, list):
                    for item in value:
                        # Si el item no es un número, es un nuevo género.
                        if item and isinstance(item, str) and not item.isdigit():
                            genero, _ = Genero.objects.get_or_create(nombre=item)
                            final_pks.append(genero.pk)
                        elif item:
                            final_pks.append(int(item))
                documento.generos.set(final_pks)
                # .set() guarda automáticamente, no necesita .save()

            else: # Para campos normales (titulo, descripcion, etc.)
                if hasattr(documento, field_name):
                    setattr(documento, field_name, value)
                    documento.save(update_fields=[field_name])
                else:
                    return JsonResponse({'success': False, 'error': f'El campo "{field_name}" no existe.'}, status=400)
            
            return JsonResponse({'success': True, 'message': f'Campo "{field_name}" guardado.'})

        except (json.JSONDecodeError, StopIteration):
            return JsonResponse({'success': False, 'error': 'Datos inválidos.'}, status=400)
        except Exception as e:
            logger.error(f"Error al autoguardar documento {pk} ({field_name}): {e}")
            return JsonResponse({'success': False, 'error': f"Error al guardar: {e}"}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

@login_required
def subir_archivo_ajax(request, pk, field_name):
    """
    Vista AJAX para subir archivos (adjunto o imagen) a un Documento existente.
    """
    if request.method == 'POST':
        try:
            documento = DocumentoUpdateView().get_queryset().get(pk=pk)
        except Documento.DoesNotExist:
            return HttpResponseForbidden("No tienes permiso para editar este documento o no existe.")

        # Asegurarnos de que el campo es válido ('adjunto' o 'imagen')
        if field_name not in ['adjunto', 'imagen']:
            return JsonResponse({'success': False, 'error': 'Campo de archivo inválido.'}, status=400)

        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'error': 'No se encontró ningún archivo.'}, status=400)
        
        # Asignamos el archivo al campo correspondiente y guardamos
        setattr(documento, field_name, file)
        documento.save(update_fields=[field_name])
        
        # Devolvemos la URL del archivo guardado para actualizar la UI
        file_url = getattr(documento, field_name).url

        return JsonResponse({'success': True, 'file_url': file_url, 'message': 'Archivo subido con éxito.'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)