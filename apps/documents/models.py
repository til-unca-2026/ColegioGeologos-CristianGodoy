from django.db import models
from django.conf import settings
from core.storage import SupabaseStorage
from .validators import validate_pdf_file


class Documento(models.Model):
    class Categoria(models.TextChoices):
        ESTATUTO = "ESTATUTO", "Estatuto"
        REGLAMENTO = "REGLAMENTO", "Reglamento"
        NORMATIVA = "NORMATIVA", "Normativa"
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
        verbose_name="Descripción",
        help_text="Explicación breve de qué contiene y para qué sirve.",
    )
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.NORMATIVA,
        verbose_name="Categoría",
    )
    numero = models.CharField(
        max_length=100,
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
        help_text="Archivo PDF guardado en Supabase Storage.",
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
        return f"{self.numero} - {self.titulo}"

