import os
from django import forms
from django.core.exceptions import ValidationError
from users.forms import validate_file
from . import models

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = models.Documento
        fields = ['titulo', 'idioma', 'grado', 'descripcion', 'adjunto', 'imagen']

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
        """
        Valida que al menos uno de los campos 'contenido' o 'adjunto' tenga datos.
        """
        cleaned_data = super().clean()
        
        descripcion = cleaned_data.get('descripcion')
        adjunto = cleaned_data.get('adjunto')

        if not descripcion and not adjunto:
            raise ValidationError(
                "Debes proporcionar un contenido de texto o adjuntar un archivo."
            )
            
        return cleaned_data
    

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = models.Comentario
        fields = ['contenido', 'adjunto_comentario', 'imagen_comentario']
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Añade tu participación aquí...'}),
        }

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