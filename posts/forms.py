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
            return validate_file(banner, ['.jpg', '.jpeg', '.png', '.webp'], 3)
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
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe tu respuesta aquí...'}),
        }
    
    def clean_banner(self):
        banner = self.cleaned_data.get('banner')
        if hasattr(banner, 'name'):
            return validate_file(banner, ['.jpg', '.jpeg', '.png', 'webp'], 3)
        return banner