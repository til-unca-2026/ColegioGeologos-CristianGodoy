import os
from datetime import date
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from core.storage import SupabaseStorage
from .validators import validate_pdf_file


class Documento(models.Model):
    class Categoria(models.TextChoices):
        LEY = "LEY", "Ley"
        ESTATUTO = "ESTATUTO", "Estatuto"
        REGLAMENTO = "REGLAMENTO", "Reglamento"
        RESOLUCION = "RESOLUCION", "Resolución"
        ACTA = "ACTA", "Acta"
        CONVENIO = "CONVENIO", "Convenio"
        ARANCEL = "ARANCEL", "Arancel"
        MODELO = "MODELO", "Modelo"
        OTRO = "OTRO", "Otro"

    class Visibilidad(models.TextChoices):
        PUBLICO = "PUBLICO", "Público"
        MATRICULADOS = "MATRICULADOS", "Matriculados"
        INTERNO = "INTERNO", "Interno"

    titulo = models.CharField(
        max_length=255,
        verbose_name="Título",
        help_text="Nombre del documento institucional.",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
        help_text="Explicación breve de qué contiene y para qué sirve.",
    )
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        verbose_name="Categoría",
    )
    numero = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Número o identificación oficial",
        help_text="Número oficial del documento, por ejemplo «Resolución 12/2024».",
    )
    fecha_documento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha del documento",
        help_text="Fecha de sanción, firma o emisión.",
    )
    vigente = models.BooleanField(
        default=True,
        verbose_name="Vigente",
        help_text="Indica si el documento está en vigor. Los reemplazados se conservan como no vigentes.",
    )
    archivo_almacenado = models.FileField(
        upload_to="documentos/",
        storage=SupabaseStorage(),
        validators=[validate_pdf_file],
        verbose_name="Archivo almacenado",
        help_text="Archivo PDF o Word (.docx/.doc).",
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=Visibilidad.choices,
        verbose_name="Visibilidad",
        help_text="PUBLICO: visible por cualquier visitante. MATRICULADOS: solo matriculados. INTERNO: colaboradores y administradores.",
    )

    # Auditoría y fechas
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de última modificación",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos_creados",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "documentos"
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-fecha_documento", "-fecha_creacion"]

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza título, número, categoría, visibilidad y descripción del documento.
        """
        if self.titulo:
            self.titulo = " ".join(self.titulo.split())
        if self.numero:
            self.numero = " ".join(self.numero.split())
        else:
            self.numero = ""
        if self.categoria:
            self.categoria = str(self.categoria).strip().upper()
        if self.visibilidad:
            self.visibilidad = str(self.visibilidad).strip().upper()
        if self.descripcion:
            self.descripcion = self.descripcion.strip()
        else:
            self.descripcion = ""

    def validar_datos(self):
        """
        Valida que el título tenga longitud adecuada y que la fecha no sea futura.
        """
        errores = {}

        if not self.titulo or len(self.titulo) < 3:
            errores["titulo"] = "El título del documento debe contener al menos 3 caracteres."

        if self.fecha_documento and self.fecha_documento > date.today():
            errores["fecha_documento"] = "La fecha del documento no puede ser una fecha futura."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.numero:
            return f"{self.numero} - {self.titulo}"
        return self.titulo

    @property
    def extension(self):
        """Devuelve la extensión en mayúscula (ej: PDF, DOCX) o cadena vacía."""
        if self.archivo_almacenado and self.archivo_almacenado.name:
            _, ext = os.path.splitext(self.archivo_almacenado.name)
            return ext.replace(".", "").upper()
        return ""

    @property
    def tipo_archivo_display(self):
        ext = self.extension
        if ext == "PDF":
            return "Documento PDF"
        elif ext in ["DOCX", "DOC"]:
            return "Documento Word"
        elif ext:
            return f"Archivo {ext}"
        return "Documento"

