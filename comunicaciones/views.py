import json
import logging
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from taggit.models import Tag
from django.utils import timezone
from django.db.models import Count

from users.mixins import GroupRequiredMixin
from .models import Publicacion, BloqueContenido
from .utils import detectar_y_limpiar_embed, validar_embed_code, obtener_info_embed
from . import forms

logger = logging.getLogger(__name__)

class PublicacionListView(ListView):
    model = Publicacion
    template_name = 'comunicaciones/publicacion_list.html'
    context_object_name = 'publicaciones'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        is_admin = user.is_authenticated and (user.is_superuser or user.groups.filter(name='Administrativo').exists())
        
        if not is_admin:
            queryset = queryset.filter(
                estado=Publicacion.ESTADO_PUBLICADO,
                fecha_publicacion__lte=timezone.now()
            )
        tag_slug = self.request.GET.get('etiqueta')
        if tag_slug:
            queryset = queryset.filter(etiquetas__slug=tag_slug)
            
        return queryset

    def get_context_data(self, **kwargs):
        """
        Añadimos la lista de etiquetas y la etiqueta activa al contexto.
        """
        context = super().get_context_data(**kwargs)
        context['todas_las_etiquetas'] = Tag.objects.annotate(
            num_publicaciones=Count('taggit_taggeditem_items')
        ).order_by('-num_publicaciones')[:15]
        context['etiqueta_activa'] = self.request.GET.get('etiqueta')
        context['now'] = timezone.now()
        
        return context

class PublicacionCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    groups_required = ['Administrativo']
    model = Publicacion
    # ================== CAMBIO: Usar el formulario simple de creación ==================
    form_class = forms.PublicacionCrearForm
    template_name = 'comunicaciones/publicacion_crear.html'

    def form_valid(self, form):
        form.instance.autor = self.request.user
        form.instance.fecha_publicacion = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('comunicaciones:editar_publicacion', kwargs={'pk': self.object.pk})

class PublicacionUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    groups_required = ['Administrativo']
    model = Publicacion
    # ================== CAMBIO: Usar el formulario completo de edición ==================
    form_class = forms.PublicacionEditarForm
    template_name = 'comunicaciones/publicacion_form.html'
    context_object_name = 'publicacion'

    def get_initial(self):
        initial = super().get_initial()
        etiquetas = self.object.etiquetas.all()
        initial['etiquetas'] = ', '.join(tag.name for tag in etiquetas)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bloques'] = self.object.bloques.all()
        context['ckeditor_form'] = forms.BloqueTextoForm()
        return context

class PublicacionDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    groups_required = ['Administrativo']
    model = Publicacion
    template_name = 'comunicaciones/confirm_delete_publicacion.html'
    success_url = reverse_lazy('comunicaciones:lista_publicaciones')


# --- Vista AJAX Todo-en-Uno ---
@login_required
def editar_publicacion_ajax(request, pk):
    if not (request.user.is_superuser or request.user.groups.filter(name='Administrativo').exists()):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    publicacion = get_object_or_404(Publicacion, pk=pk)
    
    if request.method == 'PUT':
        data = json.loads(request.body)
        
        # Primero, comprobamos si la petición es para REORDENAR bloques.
        if 'orden' in data:
            bloques_ids = [int(bid) for bid in data['orden']]
            
            if BloqueContenido.objects.filter(publicacion_id=pk, id__in=bloques_ids).count() != len(bloques_ids):
                return JsonResponse({'success': False, 'error': 'IDs de bloque no válidos'}, status=400)

            for index, bloque_id in enumerate(bloques_ids):
                BloqueContenido.objects.filter(pk=bloque_id, publicacion_id=pk).update(orden=index)
            
            logger.info(f"Bloques reordenados para publicación {pk}")
            return JsonResponse({'success': True, 'message': 'Orden guardado'})

        # Si no, es una petición para guardar los campos de la publicación.
        allowed_fields = ['titulo', 'estado', 'fecha_publicacion']
        for field, value in data.items():
            if field in allowed_fields:
                setattr(publicacion, field, value)
        
        if 'etiquetas' in data:
            tags_string = data.get('etiquetas', '')
            # Creamos una lista limpia de etiquetas a partir del string
            tag_list = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
            publicacion.etiquetas.set(tag_list)
        publicacion.save()

        return JsonResponse({'success': True, 'message': 'Publicación guardada'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def gestionar_bloque_ajax(request, **kwargs):
    if not (request.user.is_superuser or request.user.groups.filter(name='Administrativo').exists()):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")

    # ================== POST: Crear nuevo bloque ==================
    if request.method == 'POST' and 'pub_pk' in kwargs and 'file' not in request.FILES:
        pub_pk = kwargs.get('pub_pk')
        publicacion = get_object_or_404(Publicacion, pk=pub_pk)
        tipo = request.POST.get('tipo')
        
        logger.info(f"Creando bloque tipo '{tipo}' para publicación {pub_pk}")
        
        if tipo not in [t[0] for t in BloqueContenido.TIPO_BLOQUE]:
            return JsonResponse({'success': False, 'error': 'Tipo de bloque inválido'}, status=400)
            
        orden = publicacion.bloques.count()
        bloque = BloqueContenido.objects.create(publicacion=publicacion, tipo=tipo, orden=orden)
        
        logger.info(f"Bloque {bloque.pk} creado exitosamente")
        
        context = {'bloque': bloque}
        
        if tipo == 'texto':
            form = forms.BloqueTextoForm(instance=bloque)
            context['form'] = form
            
        html = render_to_string(f'comunicaciones/bloques/_{tipo}_form.html', context, request=request)
        
        return JsonResponse({'success': True, 'html': html, 'bloque_id': bloque.pk})

    # ================== PUT: Actualizar contenido o reordenar ==================
    if request.method == 'PUT':
        data = json.loads(request.body)
        
        # Caso 1: Reordenar bloques
        if 'orden' in data and 'pub_pk' in kwargs:
            pub_pk = kwargs.get('pub_pk')
            bloques_ids = [int(bid) for bid in data['orden']]
            queryset = BloqueContenido.objects.filter(publicacion_id=pub_pk, id__in=bloques_ids)
            
            if queryset.count() != len(bloques_ids):
                return JsonResponse({'success': False, 'error': 'IDs de bloque no válidos'}, status=400)

            for index, bloque_id in enumerate(bloques_ids):
                BloqueContenido.objects.filter(pk=bloque_id, publicacion_id=pub_pk).update(orden=index)
            
            logger.info(f"Bloques reordenados para publicación {pub_pk}")
            return JsonResponse({'success': True, 'message': 'Orden guardado'})
        
        # Caso 2: Actualizar el título de la publicación
        elif 'pub_pk' in kwargs and not 'bloque_pk' in kwargs:
            pub_pk = kwargs.get('pub_pk')
            publicacion = get_object_or_404(Publicacion, pk=pub_pk)
            
            allowed_fields = ['titulo', 'estado', 'fecha_publicacion', 'etiquetas']
            
            for field, value in data.items():
                if field in allowed_fields:
                    if field == 'etiquetas':
                        # Taggit necesita un tratamiento especial
                        publicacion.etiquetas.set(*[tag.strip() for tag in value.split(',')])
                    else:
                        setattr(publicacion, field, value)
            
            publicacion.save()
            logger.info(f"Publicación {pub_pk} actualizada. Campos: {list(data.keys())}")
            return JsonResponse({'success': True, 'message': 'Publicación guardada'})
        
        # Caso 3: Actualizar contenido de un bloque específico
        elif 'bloque_pk' in kwargs:
            bloque_pk = kwargs.get('bloque_pk')
            bloque = get_object_or_404(BloqueContenido, pk=bloque_pk)
            
            logger.info(f"Actualizando bloque {bloque_pk}, tipo: {bloque.tipo}")
            
            # Campos permitidos según el tipo de bloque
            allowed_fields = [
                'contenido_texto', 'contenido_embed', 'contenido_cita', 'autor_cita',
                'tamanio_imagen', 'alineacion_imagen', 'caption_imagen'
            ]
            
            updated_fields = []
            for field, value in data.items():
                if field in allowed_fields and hasattr(bloque, field):
                    
                    # Aplicar limpieza de colores problemáticos para TODO contenido de texto
                    if field == 'contenido_texto' and value:
                        preview = value[:100] if value else 'None'
                        logger.info(f"💾 Guardando contenido_texto para bloque {bloque_pk}: '{preview}...'")
                    
                    # También limpiar contenido_embed si contiene texto HTML
                    elif field == 'contenido_embed' and value:
                        # Primero validar el embed
                        is_valid, cleaned_code, error_msg = validar_embed_code(value)
                        
                        if not is_valid:
                            logger.warning(f"❌ Código embed inválido: {error_msg}")
                            return JsonResponse({
                                'success': False, 
                                'error': f'Código embed inválido: {error_msg}'
                            }, status=400)
                        
                        value = cleaned_code
                        logger.info(f"✅ Código embed validado y limpiado para bloque {bloque_pk}")
                    
                    setattr(bloque, field, value)
                    updated_fields.append(field)
            
            bloque.save()
            logger.info(f"✅ Bloque {bloque_pk} guardado. Campos: {updated_fields}")
            
            return JsonResponse({'success': True, 'message': 'Contenido guardado'})

    # ================== DELETE: Borrar un bloque ==================
    if request.method == 'DELETE' and 'bloque_pk' in kwargs:
        bloque_pk = kwargs.get('bloque_pk')
        bloque = get_object_or_404(BloqueContenido, pk=bloque_pk)
        bloque.delete()
        
        logger.info(f"Bloque {bloque_pk} eliminado")
        return JsonResponse({'success': True})
    
    # ================== POST: Subir imagen ==================
    if request.method == 'POST' and 'file' in request.FILES and 'bloque_pk' in kwargs:
        bloque_pk = kwargs.get('bloque_pk')
        bloque = get_object_or_404(BloqueContenido, pk=bloque_pk)
        
        bloque.contenido_imagen = request.FILES['file']
        bloque.save()
        
        logger.info(f"Imagen subida para bloque {bloque_pk}")

        # --- NUEVA LÓGICA ---
        # Renderizamos el HTML de los controles y lo devolvemos en la respuesta
        controls_html = render_to_string(
            'comunicaciones/bloques/_imagen_controls.html', 
            {'bloque': bloque}
        )
        
        return JsonResponse({
            'success': True, 
            'file_url': bloque.contenido_imagen.url,
            'controls_html': controls_html
        })

    logger.warning(f"Petición no manejada: {request.method} con kwargs: {kwargs}")
    return JsonResponse({'success': False, 'error': 'Petición inválida'}, status=400)

@login_required
def anclar_publicacion_ajax(request, pk):
    # Comprobación de permisos
    if not (request.user.is_superuser or request.user.groups.filter(name='Administrativo').exists()):
        return JsonResponse({'success': False, 'error': 'Permiso denegado'}, status=403)

    if request.method == 'POST':
        publicacion = get_object_or_404(Publicacion, pk=pk)
        # La lógica es simple: invertimos el valor actual del campo 'anclado'
        publicacion.anclado = not publicacion.anclado
        publicacion.save()
        
        # Devolvemos el nuevo estado
        return JsonResponse({'success': True, 'anclado': publicacion.anclado})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def preview_embed_ajax(request):
    """
    Vista AJAX para generar preview de embeds en tiempo real.
    Permite a los usuarios ver cómo se verá el embed antes de guardar.
    """
    if not (request.user.is_superuser or request.user.groups.filter(name='Administrativo').exists()):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            contenido = data.get('contenido', '')
            
            if not contenido:
                return JsonResponse({
                    'success': False,
                    'error': 'No se proporcionó contenido'
                }, status=400)
            
            # Obtener información del embed
            info = obtener_info_embed(contenido)
            
            # Convertir y limpiar
            embed_limpio = detectar_y_limpiar_embed(contenido)
            
            # Validar
            is_valid, cleaned_code, error_msg = validar_embed_code(contenido)
            
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'info': info
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'html': cleaned_code,
                'info': info,
                'message': 'Preview generado correctamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Error al generar preview: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error al generar preview: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)