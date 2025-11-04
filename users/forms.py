import re
import os
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import Organizacion, Profile, Clase, TIPO_IDENTIFICACION, PreRegistro

class UserChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        """
        Personaliza el texto que se muestra para cada usuario en el selector.
        Formato: "Apellido, Nombre (username) - ID: XXXXX"
        """
        full_name = obj.get_full_name()
        numero_id = getattr(getattr(obj, 'profile', None), 'numero_identificacion', 'N/A')
        
        if full_name:
            return f"{full_name} ({obj.username}) - ID: {numero_id}"
        else:
            return f"{obj.username} - ID: {numero_id}"

def validate_file(file, allowed_extensions, max_size_mb):
    """
    Valida la extensión y el tamaño de un archivo subido.
    """
    if file:
        # 1. Validar la extensión del archivo
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            raise ValidationError(
                f"Tipo de archivo no permitido. Solo se aceptan: {', '.join(allowed_extensions)}"
            )
        
        # 2. Validar el tamaño del archivo
        if file.size > max_size_mb * 1024 * 1024: # Convertir MB a bytes
            raise ValidationError(
                f"El archivo es demasiado grande. El tamaño máximo permitido es {max_size_mb} MB."
            )
    return file

class UserGroupForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(
        label="Roles de Usuario",
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Medida de seguridad: Excluimos la posibilidad de que un administrativo
        # se asigne a sí mismo o a otros un rol de superusuario si existiera
        # o cualquier otro grupo que no queramos que gestionen.
        self.fields['groups'].queryset = Group.objects.filter(
            name__in=['Estudiante', 'Profesor', 'Administrativo']
        )


class ClassFormForProfessor(forms.ModelForm):
    estudiantes = UserChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple,
        required=False
    )
    
    estudiantes_por_id = forms.CharField(
            label="Añadir estudiantes por ID",
            help_text="Introduce los números de identificación separados por comas o espacios.",
            required=False,
            widget=forms.Textarea(attrs={'rows': 3})
        )
    
    estudiantes_csv = forms.FileField(
        label="Añadir estudiantes desde archivo CSV",
        help_text="El archivo debe contener una única columna llamada 'numero_identificacion'.",
        required=False
    )

    def clean_estudiantes_csv(self):
        file = self.cleaned_data.get('estudiantes_csv')
        if file:
            extension = os.path.splitext(file.name)[1].lower()
            if extension != '.csv':
                raise ValidationError("El archivo debe tener la extensión .csv")
        return file
    
    class Meta:
        model = Clase
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        # Recibimos la organización de la vista
        organizacion = kwargs.pop('organizacion', None)
        super().__init__(*args, **kwargs)
        
        if organizacion:
            # Filtramos el queryset de estudiantes para mostrar solo los de esa organización
            self.fields['estudiantes'].queryset = User.objects.filter(
                profile__organizacion=organizacion,
                groups__name='Estudiante'
            ).select_related('profile')
        
        if self.instance.pk:
            self.fields['estudiantes'].initial = self.instance.estudiantes.all()

class ClassFormForAdmin(forms.ModelForm):
    estudiantes = UserChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple,
        required=False
    )
    
    estudiantes_por_id = forms.CharField(
        label="Añadir estudiantes por ID",
        help_text="Introduce los números de identificación separados por comas o espacios.",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )

    estudiantes_csv = forms.FileField(
        label="Añadir estudiantes desde archivo CSV",
        help_text="El archivo debe contener una única columna llamada 'numero_identificacion'.",
        required=False
    )

    def clean_estudiantes_csv(self):
        file = self.cleaned_data.get('estudiantes_csv')
        if file:
            extension = os.path.splitext(file.name)[1].lower()
            if extension != '.csv':
                raise ValidationError("El archivo debe tener la extensión .csv")
        return file

    class Meta:
        model = Clase
        fields = ['nombre', 'profesor']

    def __init__(self, *args, **kwargs):
        organizacion = kwargs.pop('organizacion', None)
        super().__init__(*args, **kwargs)

        if organizacion:
            # Los admins también ven solo profesores y estudiantes de la misma organización
            self.fields['profesor'].queryset = User.objects.filter(
                profile__organizacion=organizacion,
                groups__name='Profesor'
            ).select_related('profile')
            self.fields['estudiantes'].queryset = User.objects.filter(
                profile__organizacion=organizacion,
                groups__name='Estudiante'
            ).select_related('profile')
        
        if self.instance.pk:
            self.fields['estudiantes'].initial = self.instance.estudiantes.all()

class ProfileUpdateForm(forms.ModelForm):
    # Declaramos explícitamente los campos del modelo User que queremos editar
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    
    # Declaramos explícitamente los campos del modelo Profile
    avatar = forms.ImageField(required=False)
    tipo_identificacion = forms.ChoiceField(choices=Profile._meta.get_field('tipo_identificacion').choices, required=False)
    numero_identificacion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'text',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'title': 'Solo se permiten números.'
        })
    )
    adress = forms.CharField(required=False)
    telephone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-poblamos los campos del Profile con los datos existentes.
        if self.instance and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['avatar'].initial = profile.avatar
            self.fields['tipo_identificacion'].initial = profile.tipo_identificacion
            self.fields['numero_identificacion'].initial = profile.numero_identificacion
            self.fields['adress'].initial = profile.adress
            self.fields['telephone'].initial = profile.telephone
    
    def clean_numero_identificacion(self):
        """
        Reutilizamos la misma lógica de limpieza y validación aquí.
        """
        numero = self.cleaned_data.get('numero_identificacion')
        if numero:
            numero_limpio = re.sub(r'\D', '', numero)
            if not numero_limpio:
                # Puede que el campo sea opcional, así que devolvemos un string vacío
                return ""
            return numero_limpio
        return numero
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar', False)
        # Permite solo imágenes de hasta 2 MB
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        max_size_mb = 2
        return validate_file(avatar, allowed_extensions, max_size_mb)

    def save(self, commit=True):
        # Primero, guardamos la parte del User
        user = super().save(commit=commit)
        profile = user.profile
        
        # Luego, actualizamos los datos del Profile con los datos limpios del formulario
        profile.avatar = self.cleaned_data['avatar']
        profile.tipo_identificacion = self.cleaned_data['tipo_identificacion']
        profile.numero_identificacion = self.cleaned_data['numero_identificacion']
        profile.adress = self.cleaned_data['adress']
        profile.telephone = self.cleaned_data['telephone']

        if commit:
            profile.save()
            
        return user
    
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido.")
    first_name = forms.CharField(max_length=150, required=True, label="Nombres")
    last_name = forms.CharField(max_length=150, required=True, label="Apellidos")

    # Campos del modelo Profile
    tipo_identificacion = forms.ChoiceField(choices=TIPO_IDENTIFICACION, required=True, label="Tipo de Identificación")
    numero_identificacion = forms.CharField(
        max_length=20,
        required=True,
        label="Número de Identificación",
        widget=forms.TextInput(attrs={
            'type': 'text',             # Usamos 'text' para permitir el input de móviles
            'inputmode': 'numeric',     # Sugiere un teclado numérico en móviles
            'pattern': '[0-9]*',        # Patrón HTML5 para validación básica
            'title': 'Solo se permiten números.'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

    def clean_numero_identificacion(self):
        """
        Limpia y valida el número de identificación.
        """
        numero = self.cleaned_data.get('numero_identificacion')
        
        if numero:
            numero_limpio = re.sub(r'\D', '', numero)
            # Validar la entrada limpia
            if not numero_limpio:
                raise forms.ValidationError("Debes introducir un número de identificación válido.")

            if len(numero_limpio) < 5: # Añade una longitud mínima
                raise forms.ValidationError("El número de identificación parece demasiado corto.")
            return numero_limpio
        return numero

    def clean(self):
        """
        Validación a nivel de formulario para deducir la organización y
        verificar si el usuario está pre-registrado.
        """
        cleaned_data = super().clean()
        numero_id_limpio = cleaned_data.get('numero_identificacion')
        
        # Intentamos encontrar un pre-registro para este número de ID
        preregistro = PreRegistro.objects.filter(numero_identificacion=numero_id_limpio).first()

        if preregistro:
            # Si se encuentra un pre-registro...
            if preregistro.registrado:
                # ...y ya ha sido usado, lanzamos un error.
                raise forms.ValidationError("Este número de identificación ya ha sido registrado.")
            # Si no ha sido usado, guardamos la organización encontrada para usarla en el método save()
            self.organizacion_a_asignar = preregistro.organizacion
        else:
            # Si no se encuentra ningún pre-registro, es un usuario independiente.
            # Le asignamos la organización por defecto "Imago".
            imago_org, _ = Organizacion.objects.get_or_create(nombre='Imago')
            self.organizacion_a_asignar = imago_org

        return cleaned_data

    def save(self, commit=True):
        """
        Sobrescribimos el método save para usar la organización y el rol correcto.
        """
        # 1. Guardar el objeto User
        user = super().save(commit=True)
        
        # 2. Actualizar el Profile con la organización deducida y los datos extra
        user.profile.organizacion = self.organizacion_a_asignar
        user.profile.tipo_identificacion = self.cleaned_data['tipo_identificacion']
        user.profile.numero_identificacion = self.cleaned_data['numero_identificacion']
        
        # 3. Marcar el pre-registro como completado, si existía
        numero_id_limpio = self.cleaned_data.get('numero_identificacion')
        preregistro = PreRegistro.objects.filter(
            organizacion=self.organizacion_a_asignar,
            numero_identificacion=numero_id_limpio
        ).first()

        rol_a_asignar = 'Estudiante'

        if preregistro:
            rol_a_asignar = preregistro.rol_asignado
            # Marcamos el pre-registro como completado
            preregistro.registrado = True
            preregistro.save()

        try:
            grupo = Group.objects.get(name=rol_a_asignar)
            user.groups.add(grupo)
        except Group.DoesNotExist:
            grupo, _ = Group.objects.get_or_create(name=rol_a_asignar)
            user.groups.add(grupo)
        
        if commit:
            user.profile.save()
            
        return user
    
class PreRegistroAdminForm(forms.ModelForm):
    class Meta:
        model = PreRegistro
        fields = '__all__'

    def clean_numero_identificacion(self):
        """
        Limpia y valida el número de identificación, eliminando caracteres no numéricos.
        """
        numero = self.cleaned_data.get('numero_identificacion')
        if numero:
            numero_limpio = re.sub(r'\D', '', numero)
            
            if not numero_limpio:
                raise forms.ValidationError("Debes introducir un número de identificación válido.")
            return numero_limpio
        return numero
    
class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'

    def clean_numero_identificacion(self):
        """
        Reutilizamos la misma lógica de limpieza aquí.
        """
        numero = self.cleaned_data.get('numero_identificacion')
        if numero:
            numero_limpio = re.sub(r'\D', '', numero)
            
            # El campo puede ser opcional, si no queda nada, devolvemos None
            if not numero_limpio:
                return None
                
            return numero_limpio
        return numero
    
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Seleccionar Archivo CSV",
        help_text='<a href="/media/ejemplo_usuarios.csv" download>Descargar archivo de ejemplo</a>',
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    # ejemplo = forms.CharField(
    #     widget=forms.Textarea(attrs={
    #         'rows': 4,
    #         'readonly': 'readonly',
    #         'style': 'font-family: monospace; font-size: 12px; background-color: #f8f9fa;'
    #     }),
        
        # initial="numero_identificacion,email,nombre_completo,rol\n10302040,user1@ejemplo.com,Juan Pérez,administrativo\n15302030,user2@ejemplo.com,María García,estudiante",
        # label="Ejemplo de formato CSV:",
        # required=False
    # )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].help_text = format_html(
            '<a href="{}" download>📥 Descargar archivo de ejemplo</a>',
            '/static/ejemplo_usuarios.csv'  # O la URL donde tengas el archivo
        )

    def clean_csv_file(self):
        """
        Valida que el archivo subido tenga la extensión .csv.
        """
        file = self.cleaned_data.get('csv_file')
        if file:
            extension = os.path.splitext(file.name)[1].lower()
            if extension != '.csv':
                raise ValidationError("Por favor, sube un archivo con la extensión .csv")
        return file
    
class PreRegistroForm(forms.ModelForm):
    """
    Formulario para que los admins creen o editen pre-registros
    desde el panel de control.
    """
    class Meta:
        model = PreRegistro
        fields = ['numero_identificacion', 'email', 'nombre_completo', 'rol_asignado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reutilizamos la lógica de limpieza para estandarizar el ID
        self.fields['numero_identificacion'].widget.attrs.update({
            'type': 'text',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'title': 'Solo se permiten números.'
        })

    def clean_numero_identificacion(self):
        numero = self.cleaned_data.get('numero_identificacion')
        if numero:
            return re.sub(r'\D', '', numero)
        return numero