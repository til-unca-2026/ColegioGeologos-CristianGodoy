import os
from django.db import models
from django.conf import settings
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
        help_text="Explicación breve de qué contiene y para qué sirve (opcional).",
    )
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.RESOLUCION,
        verbose_name="Categoría",
    )
    numero = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Número o identificación oficial",
        help_text="Número oficial del documento, por ejemplo «Resolución 12/2024» (opcional si no aplica).",
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
        help_text="Archivo PDF o Word (.docx/.doc) guardado en Supabase Storage.",
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=Visibilidad.choices,
        default=Visibilidad.PUBLICO,
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

