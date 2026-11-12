from django import forms
from .models import Documento

INPUT_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
SELECT_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600 bg-white"
CHECKBOX_CSS = "h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
TEXTAREA_CSS = "w-full rounded-lg border border-slate-300 px-3.5 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = [
            "titulo",
            "numero",
            "categoria",
            "fecha_documento",
            "descripcion",
            "archivo_almacenado",
            "visibilidad",
            "vigente",
        ]
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Ej: Estatuto del Colegio de Geólogos de Catamarca",
            }),
            "numero": forms.TextInput(attrs={
                "class": INPUT_CSS,
                "placeholder": "Ej: Ley Prov. N° 4118 / Res. N° 05/2024",
            }),
            "categoria": forms.Select(attrs={"class": SELECT_CSS}),
            "fecha_documento": forms.DateInput(
                attrs={
                    "class": INPUT_CSS,
                    "type": "date",
                }
            ),
            "descripcion": forms.Textarea(attrs={
                "class": TEXTAREA_CSS,
                "rows": 3,
                "placeholder": "Explicación breve de qué contiene y para qué sirve este documento...",
            }),
            "archivo_almacenado": forms.ClearableFileInput(attrs={
                "class": "block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer border border-slate-300 rounded-lg p-1",
                "accept": "application/pdf",
            }),
            "visibilidad": forms.Select(attrs={"class": SELECT_CSS}),
            "vigente": forms.CheckboxInput(attrs={"class": CHECKBOX_CSS}),
        }

