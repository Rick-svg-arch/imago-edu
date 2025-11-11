import os
from django import forms
from django.core.exceptions import ValidationError
from django_select2.forms import ModelSelect2Widget, ModelSelect2TagWidget, Select2TagMixin
from users.forms import validate_file
from . import models

class AutorUnicoTagWidget(Select2TagMixin, ModelSelect2Widget):
    search_fields = ['nombre__icontains']
    queryset = models.Autor.objects.all()
    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if not value: return None
        if value.isdigit(): return value
        autor, _ = models.Autor.objects.get_or_create(nombre=value)
        return autor.pk
    def build_attrs(self, base_attrs, extra_attrs=None):
        """
        Anula los atributos por defecto para eliminar el espacio como separador.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # Por defecto, Select2TagMixin añade '[",", " "]'.
        # Lo sobrescribimos para permitir solo la coma (o ninguno si se prefiere).
        attrs['data-token-separators'] = '[","]'
        return attrs

class GeneroTagWidget(ModelSelect2TagWidget):
    queryset = models.Genero.objects.all()
    search_fields = ['nombre__icontains']
    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name)
        final_values = []
        for value in values:
            if value.isdigit(): final_values.append(value)
            else:
                genero, _ = models.Genero.objects.get_or_create(nombre=value)
                final_values.append(genero.pk)
        return final_values
class DocumentoForm(forms.ModelForm):
    class Meta:
        model = models.Documento
        fields = [
            'titulo', 'idioma', 'grado', 'autor_principal', 'generos',
            'nivel_dificultad', 'descripcion', 'adjunto', 'imagen'
        ]
        widgets = {
            'autor_principal': AutorUnicoTagWidget(attrs={'data-placeholder': 'Busca o crea un autor...'}),
            'generos': GeneroTagWidget(attrs={'data-placeholder': 'Busca o añade géneros...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_adjunto(self):
        adjunto = self.cleaned_data.get('adjunto')
        if hasattr(adjunto, 'name'):
            return validate_file(adjunto, ['.pdf', '.doc', '.docx', '.epub'], 8)
        return adjunto
    
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if hasattr(imagen, 'name'):
            return validate_file(imagen, ['.jpg', '.jpeg', '.png', '.webp'], 3)
        return imagen
    
    def clean(self):
        cleaned_data = super().clean()
        descripcion = cleaned_data.get('descripcion')
        adjunto = cleaned_data.get('adjunto')
        if not descripcion and not adjunto:
            raise ValidationError("Debes proporcionar una descripción o adjuntar un archivo.")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asignar el autor
        autor = self.cleaned_data.get('autor_nombre')
        instance.autor_principal = autor
        
        if commit:
            instance.save()
            
            # Asignar géneros (relación ManyToMany)
            generos = self.cleaned_data.get('generos_nombres', [])
            if generos:
                instance.generos.set(generos)
            else:
                instance.generos.clear()
            
            self.save_m2m()
        
        return instance


class ComentarioForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=models.Comentario.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = models.Comentario
        fields = ['contenido', 'adjunto_comentario', 'imagen_comentario', 'parent']

    def clean_adjunto_comentario(self):
        adjunto = self.cleaned_data.get('adjunto_comentario')
        if hasattr(adjunto, 'name'):
            return validate_file(adjunto, ['.pdf', '.doc', '.docx', '.epub'], 8)
        return adjunto
    
    def clean_imagen_comentario(self):
        imagen = self.cleaned_data.get('imagen_comentario')
        if hasattr(imagen, 'name'):
            return validate_file(imagen, ['.jpg', '.jpeg', '.png', '.webp'], 2)
        return imagen