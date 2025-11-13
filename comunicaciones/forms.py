from django import forms
from .models import Publicacion, BloqueContenido

class PublicacionForm(forms.ModelForm): # Cambiamos el nombre para más claridad
    """
    Formulario para la edición principal de una Publicación.
    Las etiquetas se manejan por separado para un mejor control.
    """
    # ================== CAMBIO: Definimos el campo de etiquetas manualmente ==================
    etiquetas = forms.CharField(
        required=False,
        help_text="Una lista de etiquetas separadas por comas. Ej: Eventos, Anuncios, Verano",
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Eventos, Anuncios, Verano'})
    )

    class Meta:
        model = Publicacion
        fields = ['titulo', 'estado', 'fecha_publicacion', 'etiquetas'] # Mantenemos 'etiquetas' aquí
        
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej: "Anuncio de Nuevos Talleres de Verano"'}),
            'fecha_publicacion': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'}
            ),
        }
        
        help_texts = {
            'fecha_publicacion': 'Para publicar inmediatamente, deja la fecha y hora actual. Para programar, elige una fecha y hora futura.',
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