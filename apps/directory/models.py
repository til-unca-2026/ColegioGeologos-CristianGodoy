from datetime import date
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
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
        blank=True,
        null=True,
        verbose_name="País",
    )

    class Meta:
        db_table = "universidades"
        verbose_name = "Universidad"
        verbose_name_plural = "Universidades"
        ordering = ["nombre"]

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza nombre, sigla y país de la universidad.
        """
        if self.nombre:
            self.nombre = " ".join(self.nombre.split())
        if self.sigla:
            self.sigla = " ".join(self.sigla.split())
        if self.pais:
            self.pais = str(self.pais).strip().upper()

    def validar_datos(self):
        """
        Valida que el nombre y la sigla cumplan longitudes mínimas/máximas.
        """
        errores = {}
        if not self.nombre or len(self.nombre) < 3:
            errores["nombre"] = "El nombre de la universidad debe contener al menos 3 caracteres."
        if self.sigla and not (2 <= len(self.sigla) <= 15):
            errores["sigla"] = "La sigla debe tener entre 2 y 15 caracteres."
        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza nombre y descripción de la especialidad.
        """
        if self.nombre:
            self.nombre = " ".join(self.nombre.split()).title()
        if self.descripcion:
            self.descripcion = self.descripcion.strip()
        else:
            self.descripcion = ""

    def validar_datos(self):
        """
        Valida que el nombre de la especialidad sea adecuado.
        """
        errores = {}
        if not self.nombre or len(self.nombre) < 3:
            errores["nombre"] = "El nombre de la especialidad debe contener al menos 3 caracteres."
        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

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
        null=True,
        blank=True,
        verbose_name="Fecha de matriculación",
    )
    libro = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Libro",
    )
    folio = models.PositiveIntegerField(
        null=True,
        blank=True,
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
        blank=True,
        null=True,
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

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza datos profesionales y domicilio profesional del matriculado.
        """
        if self.numero_matricula:
            self.numero_matricula = self.numero_matricula.strip().upper()

        if self.libro:
            self.libro = self.libro.strip().upper()
        else:
            self.libro = ""

        # Domicilio profesional
        if self.domicilio_profesional_calle:
            self.domicilio_profesional_calle = " ".join(self.domicilio_profesional_calle.split()).title()
        else:
            self.domicilio_profesional_calle = ""

        if self.domicilio_profesional_numero:
            self.domicilio_profesional_numero = " ".join(self.domicilio_profesional_numero.split()).upper()
        else:
            self.domicilio_profesional_numero = ""

        if self.domicilio_profesional_piso_depto:
            self.domicilio_profesional_piso_depto = " ".join(self.domicilio_profesional_piso_depto.split()).upper()
        else:
            self.domicilio_profesional_piso_depto = ""

        if self.domicilio_profesional_localidad:
            self.domicilio_profesional_localidad = " ".join(self.domicilio_profesional_localidad.split()).title()
        else:
            self.domicilio_profesional_localidad = ""

        if self.domicilio_profesional_provincia:
            self.domicilio_profesional_provincia = " ".join(self.domicilio_profesional_provincia.split()).title()
        else:
            self.domicilio_profesional_provincia = ""

        if self.domicilio_profesional_pais:
            self.domicilio_profesional_pais = str(self.domicilio_profesional_pais).strip().upper()

        if self.domicilio_profesional_cp:
            self.domicilio_profesional_cp = " ".join(self.domicilio_profesional_cp.split()).upper()
        else:
            self.domicilio_profesional_cp = ""

    def validar_datos(self):
        """
        Valida integridad de número de matrícula, folio, fechas y código postal.
        """
        errores = {}

        if not self.numero_matricula:
            errores["numero_matricula"] = "El número de matrícula es obligatorio."

        if self.fecha_matriculacion and self.fecha_matriculacion > date.today():
            errores["fecha_matriculacion"] = "La fecha de matriculación no puede ser futura."

        if self.folio is not None and self.folio <= 0:
            errores["folio"] = "El folio debe ser un número entero positivo mayor a 0."

        if self.domicilio_profesional_cp and not (4 <= len(self.domicilio_profesional_cp) <= 8):
            errores["domicilio_profesional_cp"] = "El código postal profesional debe contener entre 4 y 8 caracteres."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mat. {self.numero_matricula} - {self.usuario.get_full_name() or self.usuario.username}"

    @property
    def estado_actual(self):
        """
        Retorna el registro vigente más reciente en el historial de estados.
        Si el estado más reciente es ACTIVA pero su fecha_hasta ya expiró respecto a hoy,
        realiza una transición pasiva ('Just-in-Time') creando un nuevo registro en
        HistorialEstadoMatricula con estado SUSPENDIDA por fin de vigencia (Art. 46).
        """
        estado = self.estados.order_by("-fecha_desde", "-fecha_creacion").first()
        if not estado:
            return None

        # Evaluación de vencimiento del periodo de vigencia (Art. 46)
        if estado.estado == HistorialEstadoMatricula.Estado.ACTIVA and estado.fecha_hasta:
            from datetime import timedelta
            from django.utils import timezone
            hoy = timezone.localdate()
            if estado.fecha_hasta < hoy:
                # Transición Just-in-Time: Registrar suspensión auditable
                # La inhabilitación rige a partir del día siguiente al fin de la vigencia
                fecha_inicio_suspension = estado.fecha_hasta + timedelta(days=1)
                nuevo_estado = HistorialEstadoMatricula.objects.create(
                    matriculado=self,
                    estado=HistorialEstadoMatricula.Estado.SUSPENDIDA,
                    fecha_desde=fecha_inicio_suspension,
                    fecha_hasta=None,
                    motivo="Período de vigencia finalizado",
                    resolucion_acta=estado.resolucion_acta or "",
                    creado_por=None,
                )
                return nuevo_estado

        return estado

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
        verbose_name="Tipo de título",
    )
    emitido_por = models.ForeignKey(
        Universidad,
        on_delete=models.PROTECT,
        related_name="titulos_emitidos",
        verbose_name="Universidad emisora",
    )
    fecha_egreso = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de egreso",
    )
    fecha_expedicion = models.DateField(
        null=True,
        blank=True,
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

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza denominación y tipo de título.
        """
        if self.denominacion:
            self.denominacion = " ".join(self.denominacion.split())
        if self.tipo:
            self.tipo = str(self.tipo).strip().upper()

    def validar_datos(self):
        """
        Valida que la denominación sea consistente y coherencia cronológica de fechas.
        """
        errores = {}
        hoy = date.today()

        if not self.denominacion or len(self.denominacion) < 3:
            errores["denominacion"] = "La denominación del título debe contener al menos 3 caracteres."

        if self.fecha_egreso and self.fecha_egreso > hoy:
            errores["fecha_egreso"] = "La fecha de egreso no puede ser futura."

        if self.fecha_expedicion and self.fecha_expedicion > hoy:
            errores["fecha_expedicion"] = "La fecha de expedición no puede ser futura."

        if self.fecha_egreso and self.fecha_expedicion:
            if self.fecha_expedicion < self.fecha_egreso:
                errores["fecha_expedicion"] = "La fecha de expedición no puede ser anterior a la fecha de egreso."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.denominacion} - {self.matriculado}"


class AntecedenteDisciplinario(models.Model):
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
    descripcion = models.TextField(
        blank=True,
        default="",
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
    fecha_firmeza = models.DateField(
        verbose_name="Fecha de firmeza",
    )
    fecha_inicio_suspension = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de inicio de suspensión",
    )
    fecha_fin_suspension = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de fin de suspensión",
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
        ordering = ["-fecha_firmeza"]

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza número de expediente, tipo de sanción y descripción.
        Limpia campos no aplicables según el tipo de sanción.
        """
        if self.numero_expediente:
            self.numero_expediente = self.numero_expediente.strip().upper()
        if self.tipo_sancion:
            self.tipo_sancion = str(self.tipo_sancion).strip().upper()
        if self.descripcion:
            self.descripcion = self.descripcion.strip()
        else:
            self.descripcion = ""

        # Limpieza de campos no pertinentes al tipo de sanción
        if self.tipo_sancion != self.TipoSancion.MULTA:
            self.monto_multa = None

        if self.tipo_sancion != self.TipoSancion.SUSPENSION:
            self.fecha_inicio_suspension = None
            self.fecha_fin_suspension = None

    def validar_datos(self):
        """
        Valida expediente, fecha de firmeza, y coherencia de sanciones de multa y suspensión.
        """
        errores = {}
        hoy = date.today()

        if not self.numero_expediente or not self.numero_expediente.strip():
            errores["numero_expediente"] = "El número de expediente es obligatorio."

        if self.fecha_firmeza and self.fecha_firmeza > hoy:
            errores["fecha_firmeza"] = "La fecha de firmeza no puede ser futura."

        # Validación específica para MULTA
        if self.tipo_sancion == self.TipoSancion.MULTA:
            if self.monto_multa is None or self.monto_multa <= 0:
                errores["monto_multa"] = "Debe especificar un monto de multa mayor a 0."

        # Validación específica para SUSPENSIÓN
        if self.tipo_sancion == self.TipoSancion.SUSPENSION:
            if not self.fecha_inicio_suspension:
                errores["fecha_inicio_suspension"] = "Debe indicar la fecha de inicio de la suspensión."
            if self.fecha_inicio_suspension and self.fecha_fin_suspension:
                if self.fecha_fin_suspension < self.fecha_inicio_suspension:
                    errores["fecha_fin_suspension"] = "La fecha de finalización no puede ser anterior a la fecha de inicio de suspensión."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

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
        verbose_name="Estado",
    )
    fecha_desde = models.DateField(
        verbose_name="Fecha desde",
    )
    fecha_hasta = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha hasta",
        help_text="En ACTIVA delimita el fin del periodo de vigencia (12 meses). En SUSPENDIDA el fin de la sanción temporal.",
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
        blank=True,
        default="",
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

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def normalizar_datos(self):
        """
        Normaliza estado, motivo y resolución/acta.
        Limpia fecha_hasta si el estado es definitivo (ACTIVA o BAJA).
        """
        if self.estado:
            self.estado = str(self.estado).strip().upper()
        if self.motivo:
            self.motivo = " ".join(self.motivo.split())
        if self.resolucion_acta:
            self.resolucion_acta = " ".join(self.resolucion_acta.split()).upper()
        else:
            self.resolucion_acta = ""

        # Limpieza de fecha_hasta para estado definitivo BAJA
        if self.estado == self.Estado.BAJA:
            self.fecha_hasta = None

    def validar_datos(self):
        """
        Valida que motivo no esté vacío, coherencia de rango de fechas
        y pertenencia del antecedente disciplinario al mismo matriculado.
        """
        errores = {}

        if not self.motivo or not self.motivo.strip():
            errores["motivo"] = "El motivo del cambio de estado es obligatorio."

        if self.fecha_desde and self.fecha_hasta:
            if self.fecha_hasta < self.fecha_desde:
                errores["fecha_hasta"] = "La fecha de finalización no puede ser anterior a la fecha de inicio del estado."

        if self.origen_sancion and self.matriculado_id:
            if self.origen_sancion.matriculado_id != self.matriculado_id:
                errores["origen_sancion"] = "El antecedente disciplinario vinculado debe corresponder al mismo matriculado."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_estado_display()} desde {self.fecha_desde} - {self.matriculado}"

