from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from core.storage import SupabaseStorage


class Universidad(models.Model):
    nombre = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Nombre",
    )
    sigla = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Sigla",
    )
    pais = CountryField(
        default="AR",
        blank=True,
        verbose_name="País",
    )

    class Meta:
        db_table = "universidades"
        verbose_name = "Universidad"
        verbose_name_plural = "Universidades"
        ordering = ["nombre"]

    def __str__(self):
        if self.sigla:
            return f"{self.nombre} ({self.sigla})"
        return self.nombre


class Especialidad(models.Model):
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
    )

    class Meta:
        db_table = "especialidades"
        verbose_name = "Especialidad"
        verbose_name_plural = "Especialidades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Matriculado(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="matricula",
        verbose_name="Usuario",
    )
    numero_matricula = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de matrícula",
    )
    fecha_matriculacion = models.DateField(
        verbose_name="Fecha de matriculación",
    )
    libro = models.CharField(
        max_length=50,
        verbose_name="Libro",
    )
    folio = models.PositiveIntegerField(
        verbose_name="Folio",
    )
    especialidades = models.ManyToManyField(
        Especialidad,
        blank=True,
        related_name="matriculados",
        verbose_name="Especialidades",
    )
    jubilado = models.BooleanField(
        default=False,
        verbose_name="Jubilado",
    )

    # Domicilio profesional (Público)
    domicilio_profesional_calle = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Domicilio profesional: Calle",
    )
    domicilio_profesional_numero = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Domicilio profesional: Número",
    )
    domicilio_profesional_piso_depto = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Domicilio profesional: Piso / Depto",
    )
    domicilio_profesional_localidad = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Domicilio profesional: Localidad",
    )
    domicilio_profesional_provincia = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Domicilio profesional: Provincia",
    )
    domicilio_profesional_pais = CountryField(
        default="AR",
        blank=True,
        verbose_name="Domicilio profesional: País",
    )
    domicilio_profesional_cp = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Domicilio profesional: Código Postal",
    )

    # Auditoría
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matriculas_creadas",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matriculas_modificadas",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "matriculados"
        verbose_name = "Matriculado"
        verbose_name_plural = "Matriculados"
        ordering = ["numero_matricula"]

    def __str__(self):
        return f"Mat. {self.numero_matricula} - {self.usuario.get_full_name() or self.usuario.username}"

    @property
    def estado_actual(self):
        """Retorna el registro vigente más reciente en el historial de estados."""
        return self.estados.order_by("-fecha_desde", "-fecha_creacion").first()

    def puede_iniciar_sesion(self):
        """
        Regla de negocio (docs/11 - Modelo de datos.md):
        Un matriculado con estado BAJA o con suspensión vigente no puede iniciar sesión.
        Al finalizar la suspensión recupera el acceso automáticamente.
        Retorna (bool, str): (puede_ingresar, mensaje_motivo_en_caso_negativo).
        """
        estado = self.estado_actual
        if not estado:
            return True, ""

        from django.utils import timezone
        hoy = timezone.now().date()

        if estado.estado == HistorialEstadoMatricula.Estado.BAJA:
            return False, "Su matrícula se encuentra dada de baja. Comuníquese con la administración del Colegio."

        if estado.estado == HistorialEstadoMatricula.Estado.SUSPENDIDA:
            # Si fecha_desde <= hoy y (no hay fecha_hasta o hoy <= fecha_hasta)
            if estado.fecha_desde <= hoy:
                if not estado.fecha_hasta:
                    return False, f"Su matrícula se encuentra suspendida por tiempo indeterminado ({estado.motivo or 'Disposición del Colegio'})."
                elif hoy <= estado.fecha_hasta:
                    return False, f"Su matrícula se encuentra suspendida hasta el {estado.fecha_hasta.strftime('%d/%m/%Y')}."

        return True, ""


class Titulo(models.Model):
    class TipoTitulo(models.TextChoices):
        PREGRADO = "PREGRADO", "Pregrado"
        GRADO = "GRADO", "Grado"
        POSGRADO = "POSGRADO", "Posgrado"

    matriculado = models.ForeignKey(
        Matriculado,
        on_delete=models.CASCADE,
        related_name="titulos",
        verbose_name="Matriculado",
    )
    denominacion = models.CharField(
        max_length=200,
        verbose_name="Denominación del título",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoTitulo.choices,
        default=TipoTitulo.GRADO,
        verbose_name="Tipo de título",
    )
    emitido_por = models.ForeignKey(
        Universidad,
        on_delete=models.PROTECT,
        related_name="titulos_emitidos",
        verbose_name="Universidad emisora",
    )
    fecha_egreso = models.DateField(
        verbose_name="Fecha de egreso",
    )
    fecha_expedicion = models.DateField(
        verbose_name="Fecha de expedición del diploma",
    )
    escaneo_diploma = models.FileField(
        upload_to="diplomas/",
        storage=SupabaseStorage(),
        blank=True,
        null=True,
        verbose_name="Escaneo del diploma",
    )

    # Auditoría
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos_creados",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "titulos"
        verbose_name = "Título"
        verbose_name_plural = "Títulos"
        ordering = ["-fecha_expedicion"]

    def __str__(self):
        return f"{self.denominacion} - {self.matriculado}"


class AntecedenteDisciplinario(models.Model):
    class EstadoExpediente(models.TextChoices):
        EN_TRAMITE = "EN_TRAMITE", "En trámite"
        RESUELTO = "RESUELTO", "Resuelto"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    class TipoSancion(models.TextChoices):
        APERCIBIMIENTO = "APERCIBIMIENTO", "Apercibimiento"
        AMONESTACION = "AMONESTACION", "Amonestación"
        MULTA = "MULTA", "Multa"
        SUSPENSION = "SUSPENSION", "Suspensión"
        CANCELACION = "CANCELACION", "Cancelación"

    matriculado = models.ForeignKey(
        Matriculado,
        on_delete=models.CASCADE,
        related_name="antecedentes",
        verbose_name="Matriculado",
    )
    numero_expediente = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Número de expediente",
    )
    estado_expediente = models.CharField(
        max_length=30,
        choices=EstadoExpediente.choices,
        default=EstadoExpediente.EN_TRAMITE,
        verbose_name="Estado del expediente",
    )
    descripcion = models.TextField(
        verbose_name="Descripción de los hechos o tramitación",
    )
    tipo_sancion = models.CharField(
        max_length=30,
        choices=TipoSancion.choices,
        verbose_name="Tipo de sanción",
    )
    monto_multa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto de la multa",
    )
    fecha_inicio_sancion = models.DateField(
        verbose_name="Fecha de inicio de sanción",
    )
    fecha_fin_sancion = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de fin de sanción",
    )
    fecha_resolucion = models.DateField(
        verbose_name="Fecha de resolución",
    )
    fecha_firmeza = models.DateField(
        verbose_name="Fecha de firmeza",
    )

    # Auditoría
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="antecedentes_creados",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="antecedentes_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "antecedentes_disciplinarios"
        verbose_name = "Antecedente Disciplinario"
        verbose_name_plural = "Antecedentes Disciplinarios"
        ordering = ["-fecha_resolucion"]

    def __str__(self):
        return f"Exp. {self.numero_expediente} ({self.get_tipo_sancion_display()}) - {self.matriculado}"


class HistorialEstadoMatricula(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        SUSPENDIDA = "SUSPENDIDA", "Suspendida"
        BAJA = "BAJA", "Baja"

    matriculado = models.ForeignKey(
        Matriculado,
        on_delete=models.CASCADE,
        related_name="estados",
        verbose_name="Matriculado",
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
        verbose_name="Estado",
    )
    fecha_desde = models.DateField(
        verbose_name="Fecha desde",
    )
    fecha_hasta = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha hasta",
        help_text="Solo se completa en caso de SUSPENDIDA.",
    )
    motivo = models.CharField(
        max_length=255,
        verbose_name="Motivo",
    )
    origen_sancion = models.ForeignKey(
        AntecedenteDisciplinario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estados_originados",
        verbose_name="Origen de sanción",
    )
    resolucion_acta = models.CharField(
        max_length=150,
        verbose_name="Resolución o acta",
    )

    # Auditoría
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estados_matricula_creados",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estados_matricula_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "historial_estados_matricula"
        verbose_name = "Historial de Estado de Matrícula"
        verbose_name_plural = "Historiales de Estados de Matrícula"
        ordering = ["-fecha_desde", "-fecha_creacion"]

    def __str__(self):
        return f"{self.get_estado_display()} desde {self.fecha_desde} - {self.matriculado}"

