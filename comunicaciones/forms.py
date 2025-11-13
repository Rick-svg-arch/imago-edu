from django import forms
from .models import Publicacion, BloqueContenido

class PublicacionCrearForm(forms.ModelForm):
    """
    Formulario simple para el Paso 1. Solo captura el título y las etiquetas iniciales.
    """
    class Meta:
        model = Publicacion
        fields = ['titulo', 'etiquetas']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej: "Anuncio de Nuevos Talleres de Verano"'}),
            'etiquetas': forms.TextInput(attrs={'placeholder': 'Ej: Eventos, Anuncios, Verano'})
        }

class PublicacionEditarForm(forms.ModelForm):
    """
    Formulario completo para la página de edición. Incluye estado y programación.
    """
    etiquetas = forms.CharField(
        required=False,
        help_text="Una lista de etiquetas separadas por comas.",
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Eventos, Anuncios'})
    )

    class Meta:
        model = Publicacion
        fields = ['titulo', 'estado', 'fecha_publicacion', 'etiquetas']
        
        widgets = {
            'fecha_publicacion': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'}
            ),
        }

class BloqueTextoForm(forms.ModelForm):
    """
    Un formulario específico para renderizar el campo de texto enriquecido de un bloque,
    asegurando que se carguen los scripts de CKEditor.
    
    IMPORTANTE: Este formulario debe recibir la instancia del bloque para cargar
    el contenido existente.
    """
    class Meta:
        model = BloqueContenido
        fields = ['contenido_texto']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el widget tiene el contenido actual
        if self.instance and self.instance.pk and self.instance.contenido_texto:
            self.fields['contenido_texto'].initial = self.instance.contenido_texto