from django import forms
from users.forms import validate_file
from . import models

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = models.Categoria
        fields = ['nombre', 'descripcion']

class TemaForm(forms.ModelForm):
    class Meta:
        model = models.Tema
        fields = ['titulo', 'contenido', 'banner']
    
    def clean_banner(self):
        banner = self.cleaned_data.get('banner')
        if hasattr(banner, 'name'):
            extensiones_permitidas = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif']
            return validate_file(banner, extensiones_permitidas, 3)
        return banner

class RespuestaForm(forms.ModelForm):

    parent = forms.ModelChoiceField(
        queryset=models.Respuesta.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )
    class Meta:
        model = models.Respuesta
        fields = ['contenido', 'banner', 'parent']
    
    def clean_banner(self):
        banner = self.cleaned_data.get('banner')
        if hasattr(banner, 'name'):
            extensiones_permitidas = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif']
            return validate_file(banner, extensiones_permitidas, 3)
        return banner
    
class RespuestaEditForm(forms.ModelForm):
    """
    Un formulario específico para editar respuestas existentes.
    No incluye el campo 'parent' para evitar que se borre la anidación.
    """
    class Meta:
        model = models.Respuesta
        fields = ['contenido', 'banner']

    def clean_banner(self):
        banner = self.cleaned_data.get('banner')
        if hasattr(banner, 'name'):
            extensiones_permitidas = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif']
            return validate_file(banner, extensiones_permitidas, 3)
        return banner