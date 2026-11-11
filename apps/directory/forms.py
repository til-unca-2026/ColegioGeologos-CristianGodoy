from django import forms
from django.contrib.auth import get_user_model
from django_countries.widgets import CountrySelectWidget
from .models import (
    Matriculado,
    Titulo,
    Universidad,
    Especialidad,
    AntecedenteDisciplinario,
    HistorialEstadoMatricula,
)

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
TEXTAREA_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"


class UniversidadForm(forms.ModelForm):
    """
    Formulario para crear o editar una universidad.
    """
    class Meta:
        model = Universidad
        fields = ["nombre", "sigla", "pais"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: Universidad Nacional de Catamarca"}),
            "sigla": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: UNCa"}),
            "pais": CountrySelectWidget(attrs={"class": SELECT_CSS}),
        }


class EspecialidadForm(forms.ModelForm):
    """
    Formulario para crear o editar una especialidad geológica.
    """
    class Meta:
        model = Especialidad
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: Hidrogeología, Minería, Geotecnia..."}),
            "descripcion": forms.Textarea(attrs={"class": TEXTAREA_CSS, "rows": 2, "placeholder": "Breve descripción del área de especialización..."}),
        }


class UsuarioDniChoiceField(forms.ModelChoiceField):
    """
    ModelChoiceField personalizado para mostrar al usuario por su DNI en las opciones
    y permitir al frontend conocer el nombre completo correspondiente.
    """
    def label_from_instance(self, obj):
        dni_texto = obj.dni if obj.dni else f"Sin DNI ({obj.username})"
        return f"DNI: {dni_texto}"


class MatriculadoForm(forms.ModelForm):
    """
    Formulario para crear y editar datos profesionales de un Matriculado.
    """
    usuario = UsuarioDniChoiceField(
        queryset=User.objects.all().order_by("dni", "first_name", "last_name"),
        label="Usuario del sistema",
        required=True,
        empty_label="Seleccione un DNI...",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
        help_text="Seleccione el DNI del usuario a matricular.",
    )
    domicilio_profesional_provincia = forms.ChoiceField(
        choices=[("", "Seleccione una provincia...")] + [(p, p) for p in PROVINCIAS_ARGENTINAS],
        label="Provincia profesional",
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )

    class Meta:
        model = Matriculado
        fields = [
            "usuario",
            "numero_matricula",
            "fecha_matriculacion",
            "libro",
            "folio",
            "especialidades",
            "jubilado",
            "domicilio_profesional_calle",
            "domicilio_profesional_numero",
            "domicilio_profesional_piso_depto",
            "domicilio_profesional_localidad",
            "domicilio_profesional_provincia",
            "domicilio_profesional_pais",
            "domicilio_profesional_cp",
        ]
        widgets = {
            "numero_matricula": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: 1042"}),
            "fecha_matriculacion": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "libro": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: I"}),
            "folio": forms.NumberInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: 45", "min": "1"}),
            "especialidades": forms.SelectMultiple(attrs={"class": f"{SELECT_CSS} min-h-[110px]"}),
            "jubilado": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
            "domicilio_profesional_calle": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Calle"}),
            "domicilio_profesional_numero": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Número"}),
            "domicilio_profesional_piso_depto": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Piso / Depto / Oficina"}),
            "domicilio_profesional_localidad": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ciudad / Localidad"}),
            "domicilio_profesional_pais": CountrySelectWidget(attrs={"class": SELECT_CSS}),
            "domicilio_profesional_cp": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Código Postal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["usuario"].disabled = True
            self.fields["usuario"].help_text = "El usuario vinculado no puede modificarse una vez creada la matrícula."
        else:
            usuarios_ya_matriculados = Matriculado.objects.values_list("usuario_id", flat=True)
            self.fields["usuario"].queryset = User.objects.exclude(id__in=usuarios_ya_matriculados).order_by(
                "dni", "first_name", "last_name"
            )


class TituloForm(forms.ModelForm):
    """
    Formulario para carga y edición de títulos de un matriculado.
    """
    class Meta:
        model = Titulo
        fields = [
            "denominacion",
            "tipo",
            "emitido_por",
            "fecha_egreso",
            "fecha_expedicion",
            "escaneo_diploma",
        ]
        widgets = {
            "denominacion": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: Licenciado en Geología"}),
            "tipo": forms.Select(attrs={"class": SELECT_CSS}),
            "emitido_por": forms.Select(attrs={"class": SELECT_CSS}),
            "fecha_egreso": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "fecha_expedicion": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "escaneo_diploma": forms.ClearableFileInput(attrs={
                "class": "w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
            }),
        }


class HistorialEstadoMatriculaForm(forms.ModelForm):
    """
    Formulario para registrar cambios en el estado de una matrícula (Activa, Suspendida, Baja).
    """
    class Meta:
        model = HistorialEstadoMatricula
        fields = [
            "estado",
            "fecha_desde",
            "fecha_hasta",
            "motivo",
            "origen_sancion",
            "resolucion_acta",
        ]
        widgets = {
            "estado": forms.Select(attrs={"class": SELECT_CSS}),
            "fecha_desde": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "fecha_hasta": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "motivo": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: Alta ordinaria de matrícula / Sanción disciplinaria"}),
            "origen_sancion": forms.Select(attrs={"class": SELECT_CSS}),
            "resolucion_acta": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: Resolución CD N° 15/2026"}),
        }

    def __init__(self, matriculado, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["origen_sancion"].queryset = AntecedenteDisciplinario.objects.filter(matriculado=matriculado)
        self.fields["origen_sancion"].required = False
        self.fields["origen_sancion"].empty_label = "Sin antecedente asociado (Opcional)"


class AntecedenteDisciplinarioForm(forms.ModelForm):
    """
    Formulario para registrar antecedentes disciplinarios.
    """
    class Meta:
        model = AntecedenteDisciplinario
        fields = [
            "numero_expediente",
            "estado_expediente",
            "tipo_sancion",
            "monto_multa",
            "fecha_inicio_sancion",
            "fecha_fin_sancion",
            "fecha_resolucion",
            "fecha_firmeza",
            "descripcion",
        ]
        widgets = {
            "numero_expediente": forms.TextInput(attrs={"class": INPUT_CSS, "placeholder": "Ej: EXP-2026-004"}),
            "estado_expediente": forms.Select(attrs={"class": SELECT_CSS}),
            "tipo_sancion": forms.Select(attrs={"class": SELECT_CSS}),
            "monto_multa": forms.NumberInput(attrs={"class": INPUT_CSS, "placeholder": "0.00", "step": "0.01"}),
            "fecha_inicio_sancion": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "fecha_fin_sancion": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "fecha_resolucion": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "fecha_firmeza": forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT_CSS, "type": "date"}),
            "descripcion": forms.Textarea(attrs={"class": TEXTAREA_CSS, "rows": 3, "placeholder": "Detalle explicativo de los hechos..."}),
        }
