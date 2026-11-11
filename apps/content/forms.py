from django import forms
from django.utils import timezone
from .models import Contenido, DetalleEvento, ImagenContenido

INPUT_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
SELECT_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600 bg-white"
CHECKBOX_CSS = "h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
TEXTAREA_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ContenidoForm(forms.ModelForm):
    # Imagen de portada opcional integrada en el formulario principal
    imagen_portada = forms.ImageField(
        required=False,
        label="Imagen de portada",
        help_text="Formatos recomendados: JPG, PNG o WEBP.",
        widget=forms.ClearableFileInput(attrs={
            "class": "block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer border border-slate-300 rounded-lg p-1",
            "accept": "image/*",
        }),
    )
    texto_alt_portada = forms.CharField(
        required=False,
        max_length=255,
        label="Texto alternativo de la imagen",
        help_text="Descripción para accesibilidad (lectores de pantalla).",
        widget=forms.TextInput(attrs={
            "class": INPUT_CSS,
            "placeholder": "Ej: Foto grupal en la apertura de la jornada de minería",
        }),
    )
    epigrafe_portada = forms.CharField(
        required=False,
        max_length=255,
        label="Epígrafe / Pie de foto",
        widget=forms.TextInput(attrs={
            "class": INPUT_CSS,
            "placeholder": "Ej: Comisión directiva junto a los expositores invitados",
        }),
    )

    # Imágenes adicionales para la galería
    imagenes_galeria = MultipleFileField(
        required=False,
        label="Imágenes adicionales (Galería)",
        help_text="Podés seleccionar varias imágenes al mismo tiempo para la galería.",
        widget=MultipleFileInput(attrs={
            "class": "block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer border border-slate-300 rounded-lg p-1",
            "accept": "image/*",
        }),
    )

    class Meta:
        model = Contenido
        fields = [
            "tipo",
            "titulo",
            "resumen",
            "cuerpo",
            "fecha_publicacion",
            "visibilidad",
            "destacado",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": SELECT_CSS, "id": "id_tipo"}),
            "titulo": forms.TextInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Ej: Convocatoria a la Asamblea General Ordinaria 2026",
            }),
            "resumen": forms.Textarea(attrs={
                "class": TEXTAREA_CSS,
                "rows": 2,
                "placeholder": "Breve resumen para el listado y tarjetas en la portada...",
            }),
            "cuerpo": forms.HiddenInput(attrs={"id": "id_cuerpo"}),
            "fecha_publicacion": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "class": INPUT_CSS,
                    "type": "datetime-local",
                    "id": "id_fecha_publicacion",
                },
            ),
            "visibilidad": forms.Select(attrs={"class": SELECT_CSS}),
            "destacado": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear el valor inicial para datetime-local convirtiendo a hora local (Argentina/Catamarca)
        if self.instance and self.instance.pk:
            if self.instance.fecha_publicacion:
                fecha_local = timezone.localtime(self.instance.fecha_publicacion)
                self.initial["fecha_publicacion"] = fecha_local.strftime("%Y-%m-%dT%H:%M")

            # Pre-cargar datos de la portada existente si los tiene
            portada = self.instance.imagenes.filter(es_portada=True).first()
            if portada:
                self.initial["texto_alt_portada"] = portada.texto_alt
                self.initial["epigrafe_portada"] = portada.epigrafe


class DetalleEventoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los campos no son required a nivel HTML para no bloquear submit en modo Noticia/Novedad
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = DetalleEvento
        fields = [
            "inicio",
            "fin",
            "lugar",
            "modalidad",
            "link_inscripcion",
            "cupo",
        ]
        widgets = {
            "inicio": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"class": INPUT_CSS, "type": "datetime-local"},
            ),
            "fin": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"class": INPUT_CSS, "type": "datetime-local"},
            ),
            "lugar": forms.TextInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Ej: Sede del Colegio, Salón Auditorio / Enlace Meet",
            }),
            "modalidad": forms.Select(attrs={"class": SELECT_CSS}),
            "link_inscripcion": forms.URLInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "https://forms.gle/...",
            }),
            "cupo": forms.NumberInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Dejar vacío si no hay límite",
                "min": 1,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get("inicio")
        lugar = cleaned_data.get("lugar")
        modalidad = cleaned_data.get("modalidad")
        fin = cleaned_data.get("fin")

        # Si se completó algo de evento, inicio y lugar son requeridos
        if not inicio:
            self.add_error("inicio", "La fecha y hora de inicio es requerida para eventos.")
        if not lugar:
            self.add_error("lugar", "El lugar o plataforma es requerido.")
        if not modalidad:
            self.add_error("modalidad", "Debe indicar la modalidad.")

        if inicio and fin and fin < inicio:
            self.add_error("fin", "La fecha de fin no puede ser anterior a la fecha de inicio.")
        return cleaned_data
