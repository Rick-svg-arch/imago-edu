import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from .models import Documento, Comentario, ELEGIR_GRADO, ELEGIR_IDIOMA
from . import forms
from .decorators import group_required
from .mixins import UserIsAuthorMixin


def serve_file(request, pk):
    """
    Vista dedicada a servir el archivo adjunto
    """
    documento = get_object_or_404(Documento, pk=pk)
    if not documento.adjunto:
        raise Http404("El documento no tiene un archivo adjunto.")

    file_path = documento.adjunto.path

    if os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain; charset=utf-8',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        
        content_type = content_types.get(ext, 'application/octet-stream')
        
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type=content_type)

            response['X-Frame-Options'] = 'SAMEORIGIN'

            if ext == '.txt':
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            else:
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
                
            return response
    else:
        raise Http404("El archivo no fue encontrado en el servidor.")


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
        """
        Añadimos datos extra al contexto para usarlos en la plantilla.
        """
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
        
        comentarios_list = self.get_object().comentarios.order_by('-fecha_creacion')
        paginator = Paginator(comentarios_list, 10) #Numero de comentarios por paginación
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['comentarios_page'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages() # Para que el include funcione
        context['page_obj'] = page_obj # El include necesita 'page_obj'

        context['comentario_form'] = forms.ComentarioForm()
        return context


@login_required
@group_required(['Profesor', 'Administrativo'])
def subir_documento(request):
    if request.method == 'POST':
        form = forms.DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo_documento = form.save(commit=False)
            nuevo_documento.author = request.user
            nuevo_documento.save()
            return redirect('lecturas:lista_documentos_base')
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