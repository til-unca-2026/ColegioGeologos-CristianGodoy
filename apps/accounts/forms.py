from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django_countries.widgets import CountrySelectWidget
from .models import MembresiaComision

User = get_user_model()

PROVINCIAS_ARGENTINAS = [
    "Catamarca",
    "Buenos Aires",
    "Ciudad Autónoma de Buenos Aires",
    "Chaco",
    "Chubut",
    "Córdoba",
    "Corrientes",
    "Entre Ríos",
    "Formosa",
    "Jujuy",
    "La Pampa",
    "La Rioja",
    "Mendoza",
    "Misiones",
    "Neuquén",
    "Río Negro",
    "Salta",
    "San Juan",
    "San Luis",
    "Santa Cruz",
    "Santa Fe",
    "Santiago del Estero",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur",
    "Tucumán",
]

INPUT_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
SELECT_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600 bg-white"
CHECKBOX_CSS = "h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"


class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulario de autenticación que valida las credenciales y además hace cumplir
    la regla de negocio de Matrícula (docs/11 - Modelo de datos.md):
    Un matriculado con estado BAJA o con suspensión vigente no puede iniciar sesión.
    """
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        # Verificamos si el usuario tiene matrícula asociada
        if hasattr(user, "matricula"):
            matricula = user.matricula
            puede, motivo = matricula.puede_iniciar_sesion()
            if not puede:
                raise ValidationError(
                    motivo,
                    code="matricula_inhabilitada",
                )


class AdminUserCreateForm(forms.ModelForm):
    """
    Formulario para que un administrador cree un nuevo usuario desde el Dashboard.
    Incluye todos los campos de identidad (Ley 25.326), contacto, preferencias de visibilidad,
    domicilio real, seguridad y asignación de grupo institucional de Django (Matriculados,
    Colaboradores o Administradores).
    
    IMPORTANTE: Ningún usuario es staff; is_staff = False siempre salvo superusuario dev.
    """
    password = forms.CharField(
        label="Contraseña inicial",
        widget=forms.PasswordInput(attrs={
            "class": INPUT_CSS,
            "placeholder": "Ingrese una contraseña inicial segura",
            "autocomplete": "new-password",
        }),
        required=True,
        help_text="Mínimo 8 caracteres. El usuario podrá y deberá cambiarla en su primer login.",
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.exclude(name__iexact="matriculados").order_by("name"),
        label="Rol / Grupo especial (Opcional)",
        required=False,
        empty_label="Sin grupo especial (Usuario estándar / Pendiente de matriculación)",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
        help_text="Opcional. Seleccione solo si el usuario cumplirá funciones especiales (Administradores o Colaboradores). El rol 'Matriculados' se asigna automáticamente al crear la matrícula.",
    )

    class Meta:
        model = User
        fields = [
            # Credenciales y cuenta
            "username",
            "email",
            "password",
            # Identidad básica
            "first_name",
            "last_name",
            "dni",
            # Identidad complementaria (Opcional)
            "cuil_cuit",
            "fecha_nacimiento",
            "lugar_nacimiento",
            "nacionalidad",
            # Contacto y foto (Opcional)
            "phone",
            "profile_picture",
            # Domicilio real (Opcional)
            "domicilio_real_calle",
            "domicilio_real_numero",
            "domicilio_real_piso_depto",
            "domicilio_real_localidad",
            "domicilio_real_provincia",
            "domicilio_real_pais",
            "domicilio_real_cp",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "ej: jgomez o nro_dni"}),
            "email": forms.EmailInput(attrs={"class": INPUT_CSS, "placeholder": "correo@ejemplo.com"}),
            "first_name": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Nombre(s)"}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Apellido(s)"}),
            "dni": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Número de documento sin puntos"}),
            "cuil_cuit": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "ej: 20-12345678-9"}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": INPUT_CSS, "type": "date"}),
            "lugar_nacimiento": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Localidad, Provincia, País"}),
            "phone": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "+54 383 4123456"}),
            "profile_picture": forms.FileInput(attrs={"class": "w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"}),
            "nacionalidad": CountrySelectWidget(attrs={"class": SELECT_CSS}),
            "domicilio_real_calle": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Nombre de calle"}),
            "domicilio_real_numero": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "1234"}),
            "domicilio_real_piso_depto": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Piso / Depto (opcional)"}),
            "domicilio_real_localidad": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ciudad o localidad"}),
            "domicilio_real_provincia": forms.TextInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Seleccione o escriba la provincia/región...",
                "list": "lista-provincias-argentinas",
            }),
            "domicilio_real_pais": CountrySelectWidget(attrs={"class": SELECT_CSS}),
            "domicilio_real_cp": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Código Postal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo lo estrictamente esencial es obligatorio
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["dni"].required = True
        # Todo lo demás es opcional para no trabar la creación
        self.fields["cuil_cuit"].required = False
        self.fields["fecha_nacimiento"].required = False
        self.fields["lugar_nacimiento"].required = False
        self.fields["domicilio_real_calle"].required = False
        self.fields["domicilio_real_numero"].required = False
        self.fields["domicilio_real_localidad"].required = False
        self.fields["domicilio_real_provincia"].required = False
        self.fields["domicilio_real_cp"].required = False

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def clean_dni(self):
        dni = (self.cleaned_data.get("dni") or "").strip()
        if dni:
            if User.objects.filter(dni=dni).exists():
                raise ValidationError("Ya existe un usuario registrado con este número de DNI.")
            return dni
        return None

    def clean_cuil_cuit(self):
        cuil_cuit = (self.cleaned_data.get("cuil_cuit") or "").strip()
        if cuil_cuit:
            if User.objects.filter(cuil_cuit=cuil_cuit).exists():
                raise ValidationError("Ya existe un usuario registrado con este CUIL/CUIT.")
            return cuil_cuit
        return None

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        # Regla de seguridad y estado por defecto
        user.is_staff = False
        user.is_active = True
        user.must_change_password = True

        # Privacidad por defecto: los datos nacen privados
        user.publicar_email = False
        user.publicar_telefono = False

        group = self.cleaned_data.get("group")
        if commit:
            user.save()
            if group:
                user.groups.set([group])
            else:
                user.groups.clear()

        return user


class AdminUserEditForm(forms.ModelForm):
    """
    Formulario para editar un usuario existente desde el Dashboard administrativo.
    Permite modificar datos de identidad (Ley 25.326), contacto, visibilidad, domicilio real,
    estado de la cuenta y reasignar el grupo de acceso de Django.
    """
    group = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"),
        label="Rol / Grupo de acceso",
        required=False,
        empty_label="Sin grupo asignado",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
        help_text="Seleccione el grupo al que pertenece el usuario (Matriculados, Colaboradores o Administradores).",
    )
    new_password = forms.CharField(
        label="Nueva contraseña (opcional)",
        widget=forms.PasswordInput(attrs={
            "class": INPUT_CSS,
            "placeholder": "Dejar en blanco para mantener la contraseña actual",
            "autocomplete": "new-password",
        }),
        required=False,
        help_text="Complete este campo solo si desea resetear manualmente la contraseña del usuario.",
    )

    class Meta:
        model = User
        fields = [
            # Credenciales y cuenta
            "username",
            "email",
            # Identidad (Ley 25.326)
            "first_name",
            "last_name",
            "dni",
            "cuil_cuit",
            "fecha_nacimiento",
            "lugar_nacimiento",
            "nacionalidad",
            # Contacto y visibilidad
            "phone",
            "publicar_email",
            "publicar_telefono",
            "profile_picture",
            # Domicilio real (Ley 25.326)
            "domicilio_real_calle",
            "domicilio_real_numero",
            "domicilio_real_piso_depto",
            "domicilio_real_localidad",
            "domicilio_real_provincia",
            "domicilio_real_pais",
            "domicilio_real_cp",
            # Estado y Seguridad
            "must_change_password",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT_CSS}),
            "email": forms.EmailInput(attrs={"class": INPUT_CSS}),
            "first_name": forms.TextInput(attrs={"class": INPUT_CSS}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CSS}),
            "dni": forms.TextInput(attrs={"class": INPUT_CSS}),
            "cuil_cuit": forms.TextInput(attrs={"class": INPUT_CSS}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": INPUT_CSS, "type": "date"}),
            "lugar_nacimiento": forms.TextInput(attrs={"class": INPUT_CSS}),
            "phone": forms.TextInput(attrs={"class": INPUT_CSS}),
            "profile_picture": forms.FileInput(attrs={"class": "w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"}),
            "nacionalidad": CountrySelectWidget(attrs={"class": SELECT_CSS}),
            "domicilio_real_calle": forms.TextInput(attrs={"class": INPUT_CSS}),
            "domicilio_real_numero": forms.TextInput(attrs={"class": INPUT_CSS}),
            "domicilio_real_piso_depto": forms.TextInput(attrs={"class": INPUT_CSS}),
            "domicilio_real_localidad": forms.TextInput(attrs={"class": INPUT_CSS}),
            "domicilio_real_provincia": forms.TextInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Seleccione o escriba la provincia/región...",
                "list": "lista-provincias-argentinas",
            }),
            "domicilio_real_pais": CountrySelectWidget(attrs={"class": SELECT_CSS}),
            "domicilio_real_cp": forms.TextInput(attrs={"class": INPUT_CSS}),
            "publicar_email": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
            "publicar_telefono": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
            "must_change_password": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

        if self.instance and self.instance.pk:
            current_group = self.instance.groups.first()
            if current_group:
                self.fields["group"].initial = current_group

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe otro usuario registrado con este correo electrónico.")
        return email

    def clean_dni(self):
        dni = (self.cleaned_data.get("dni") or "").strip()
        qs = User.objects.filter(dni=dni)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if dni and qs.exists():
            raise ValidationError("Ya existe otro usuario registrado con este número de DNI.")
        return dni if dni else None

    def clean_cuil_cuit(self):
        cuil_cuit = (self.cleaned_data.get("cuil_cuit") or "").strip()
        qs = User.objects.filter(cuil_cuit=cuil_cuit)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if cuil_cuit and qs.exists():
            raise ValidationError("Ya existe otro usuario registrado con este CUIL/CUIT.")
        return cuil_cuit if cuil_cuit else None

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)

        # Regla: ningún usuario es staff, salvo si ya era superuser dev
        if not user.is_superuser:
            user.is_staff = False

        group = self.cleaned_data.get("group")
        if commit:
            user.save()
            if group:
                user.groups.set([group])
            else:
                user.groups.clear()

        return user


class MembresiaComisionForm(forms.ModelForm):
    """
    Formulario para asignar o editar cargos dentro de las Comisiones (Directiva, Revisora de Cuentas) desde el Dashboard.
    """
    class Meta:
        model = MembresiaComision
        fields = [
            "usuario",
            "comision",
            "cargo",
            "fecha_desde",
            "fecha_hasta",
        ]
        widgets = {
            "usuario": forms.Select(attrs={"class": SELECT_CSS}),
            "comision": forms.Select(attrs={"class": SELECT_CSS}),
            "cargo": forms.Select(attrs={"class": SELECT_CSS}),
            "fecha_desde": forms.DateInput(attrs={"class": INPUT_CSS, "type": "date"}),
            "fecha_hasta": forms.DateInput(attrs={"class": INPUT_CSS, "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar usuarios activos ordenados por apellido/nombre o username
        self.fields["usuario"].queryset = User.objects.filter(is_active=True).order_by("last_name", "first_name", "username")
        self.fields["usuario"].label_from_instance = lambda u: f"{u.get_full_name() or u.username} ({u.dni or '@' + u.username})"
        self.fields["fecha_desde"].required = True
        self.fields["fecha_hasta"].required = False
        self.fields["fecha_hasta"].help_text = "Dejar en blanco si el mandato continúa vigente."

    def clean(self):
        cleaned_data = super().clean()
        comision = cleaned_data.get("comision")
        cargo = cleaned_data.get("cargo")
        fecha_desde = cleaned_data.get("fecha_desde")
        fecha_hasta = cleaned_data.get("fecha_hasta")

        if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
            raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de asunción.")

        # Validación cruzada entre Comisión y Cargo
        cargos_revisora = [
            MembresiaComision.Cargo.REVISOR_TITULAR_1,
            MembresiaComision.Cargo.REVISOR_TITULAR_2,
            MembresiaComision.Cargo.REVISOR_SUPLENTE_1,
            MembresiaComision.Cargo.REVISOR_SUPLENTE_2,
        ]

        if comision == MembresiaComision.Comision.REVISORA_CUENTAS:
            if cargo not in cargos_revisora:
                raise ValidationError({"cargo": "El cargo seleccionado no corresponde a la Comisión Revisora de Cuentas."})
        elif comision == MembresiaComision.Comision.DIRECTIVA:
            if cargo in cargos_revisora:
                raise ValidationError({"cargo": "El cargo seleccionado no corresponde a la Comisión Directiva."})

        return cleaned_data


class UserProfileUpdateForm(forms.ModelForm):
    """
    Formulario de autogestión para que el propio usuario actualice sus datos
    de contacto, visibilidad, foto de perfil y domicilio real desde el Dashboard.
    Los datos legales de identidad (DNI, CUIL, Nombre, Nacimiento) no se exponen aquí.
    """
    domicilio_real_provincia = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CSS,
                "list": "provincias-perfil-list",
                "placeholder": "Seleccionar o escribir provincia",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "profile_picture",
            "email",
            "phone",
            "publicar_email",
            "publicar_telefono",
            "domicilio_real_calle",
            "domicilio_real_numero",
            "domicilio_real_piso_depto",
            "domicilio_real_localidad",
            "domicilio_real_provincia",
            "domicilio_real_pais",
            "domicilio_real_cp",
        ]
        widgets = {
            "profile_picture": forms.FileInput(attrs={"class": INPUT_CSS, "accept": "image/*"}),
            "email": forms.EmailInput(attrs={"class": INPUT_CSS, "placeholder": "ejemplo@correo.com"}),
            "phone": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "+54 383 4123456"}),
            "publicar_email": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
            "publicar_telefono": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
            "domicilio_real_calle": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Nombre de la calle"}),
            "domicilio_real_numero": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "123"}),
            "domicilio_real_piso_depto": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "2 B"}),
            "domicilio_real_localidad": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "San Fernando del Valle"}),
            "domicilio_real_pais": CountrySelectWidget(attrs={"class": SELECT_CSS}),
            "domicilio_real_cp": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "K4700"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["domicilio_real_pais"].initial = self.instance.domicilio_real_pais or "AR"

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Este correo electrónico ya está registrado por otro usuario.")
        return email
