import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.conf import settings
from django.core.files.storage import default_storage
from .models import Documento, Comentario, ELEGIR_GRADO, ELEGIR_IDIOMA
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
        logger.info(f"=== DETALLE DOCUMENTO {doc.pk} ===")
        logger.info(f"Tiene adjunto: {bool(doc.adjunto)}")
        if doc.adjunto:
            logger.info(f"Adjunto name: {doc.adjunto.name}")
            logger.info(f"Adjunto URL: {doc.adjunto.url}")
        
        comentarios_list = doc.comentarios.order_by('-fecha_creacion')
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
        logger.info(f"FILES en request: {request.FILES.keys()}")
        
        form = forms.DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Formulario válido, guardando...")
            nuevo_documento = form.save(commit=False)
            nuevo_documento.author = request.user
            
            logger.info(f"Antes de save - Adjunto: {nuevo_documento.adjunto}")
            nuevo_documento.save()
            logger.info(f"Después de save - Adjunto name: {nuevo_documento.adjunto.name if nuevo_documento.adjunto else 'None'}")
            logger.info(f"Después de save - Adjunto URL: {nuevo_documento.adjunto.url if nuevo_documento.adjunto else 'None'}")
            
            # Verificar en storage
            if nuevo_documento.adjunto:
                try:
                    exists = default_storage.exists(nuevo_documento.adjunto.name)
                    logger.info(f"Archivo existe en storage después de guardar: {exists}")
                    
                    if exists:
                        size = default_storage.size(nuevo_documento.adjunto.name)
                        logger.info(f"Tamaño del archivo: {size} bytes")
                except Exception as e:
                    logger.error(f"Error verificando archivo en storage: {e}")
            
            return redirect('lecturas:lista_documentos_base')
        else:
            logger.error(f"Formulario inválido: {form.errors}")
    else:
        form = forms.DocumentoForm()
    
    return render(request, 'lecturas/subir_documento.html', {'form_lecturas': form})


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
            return redirect('lecturas:detalle_documento', pk=documento.pk)
    
    return redirect('lecturas:detalle_documento', pk=documento.pk)


class DocumentoUpdateView(LoginRequiredMixin, UserIsAuthorMixin, UpdateView):
    model = Documento
    form_class = forms.DocumentoForm
    template_name = 'lecturas/documento_form.html'

    def get_success_url(self):
        return reverse_lazy('lecturas:detalle_documento', kwargs={'pk': self.object.pk})
    

class DocumentoDeleteView(LoginRequiredMixin, UserIsAuthorMixin, DeleteView):
    model = Documento
    template_name = 'lecturas/documento_confirm_delete.html' 
    success_url = reverse_lazy('lecturas:lista_documentos_base')


class ComentarioUpdateView(LoginRequiredMixin, UserIsAuthorMixin, UpdateView):
    model = Comentario
    form_class = forms.ComentarioForm
    template_name = 'lecturas/comentario_form.html'

    def get_success_url(self):
        return reverse_lazy('lecturas:detalle_documento', kwargs={'pk': self.object.documento.pk})


class ComentarioDeleteView(LoginRequiredMixin, UserIsAuthorMixin, DeleteView):
    model = Comentario
    template_name = 'lecturas/comentario_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('lecturas:detalle_documento', kwargs={'pk': self.object.documento.pk})