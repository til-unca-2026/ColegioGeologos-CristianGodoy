import re
from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from core.storage import SupabaseStorage


class User(AbstractUser):
    # Identificación y datos personales (Ley 25.326)
    dni = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="DNI / Documento",
    )
    cuil_cuit = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="CUIL / CUIT",
    )
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de nacimiento",
    )
    lugar_nacimiento = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Lugar de nacimiento",
    )
    nacionalidad = CountryField(
        blank=True,
        null=True,
        verbose_name="Nacionalidad",
    )

    # Contacto y preferencias públicas
    phone = PhoneNumberField(
        blank=True,
        null=True,
        region="AR",
        verbose_name="Teléfono",
        help_text="Formato internacional E.164 (ej: +54 383 4123456 o 3834123456)",
    )
    publicar_email = models.BooleanField(
        default=False,
        verbose_name="Publicar email",
    )
    publicar_telefono = models.BooleanField(
        default=False,
        verbose_name="Publicar teléfono",
    )
    profile_picture = models.ImageField(
        upload_to="profiles/",
        storage=SupabaseStorage(),
        blank=True,
        null=True,
        verbose_name="Foto de perfil",
    )

    # Seguridad y control de acceso
    must_change_password = models.BooleanField(
        default=True,
        verbose_name="Debe cambiar la contraseña",
    )

    # Domicilio real (Ley 25.326)
    domicilio_real_calle = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Domicilio real: Calle",
    )
    domicilio_real_numero = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Domicilio real: Número",
    )
    domicilio_real_piso_depto = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Domicilio real: Piso / Depto",
    )
    domicilio_real_localidad = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Domicilio real: Localidad",
    )
    domicilio_real_provincia = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Domicilio real: Provincia",
    )
    domicilio_real_pais = CountryField(
        blank=True,
        null=True,
        verbose_name="Domicilio real: País",
    )
    domicilio_real_cp = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Domicilio real: Código Postal",
    )

    # Auditoría
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de última modificación",
    )
    creado_por = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios_creados",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def validar_datos(self):
        """
        Aplica validaciones de integridad y reglas de negocio para User.
        """
        errores = {}

        # 1. Email
        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                errores["email"] = "Ingrese una dirección de correo electrónico válida."

        # 2. DNI
        if self.dni:
            if not (7 <= len(self.dni) <= 9 and self.dni.isdigit()):
                errores["dni"] = "El DNI debe contener entre 7 y 9 dígitos numéricos."

        # 3. CUIL / CUIT (11 dígitos numéricos si está presente)
        if self.cuil_cuit:
            cuil_digits = re.sub(r"\D", "", self.cuil_cuit)
            if len(cuil_digits) != 11:
                errores["cuil_cuit"] = "El CUIL/CUIT debe contener 11 dígitos numéricos."
            elif self.dni and self.dni.isdigit():
                # Coherencia entre DNI y número central de CUIL (8 dígitos)
                dni_padding = self.dni.zfill(8)
                if cuil_digits[2:10] != dni_padding:
                    errores["cuil_cuit"] = f"El CUIL/CUIT no coincide con el DNI ingresado ({self.dni})."

        # 4. Fecha de nacimiento
        if self.fecha_nacimiento:
            hoy = date.today()
            if self.fecha_nacimiento > hoy:
                errores["fecha_nacimiento"] = "La fecha de nacimiento no puede ser una fecha futura."
            else:
                edad = hoy.year - self.fecha_nacimiento.year - (
                    (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
                if edad < 18:
                    errores["fecha_nacimiento"] = "El usuario debe tener al menos 18 años de edad."

        # 5. Código Postal
        if self.domicilio_real_cp:
            if not (4 <= len(self.domicilio_real_cp) <= 8):
                errores["domicilio_real_cp"] = "El código postal debe contener entre 4 y 8 caracteres."

        if errores:
            raise ValidationError(errores)

    def normalizar_datos(self):
        """
        Aplica normalización de datos para garantizar consistencia antes de persistir.
        """
        # 1. Campos heredados de AbstractUser
        if self.username:
            self.username = self.username.strip().lower()

        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = ""

        if self.first_name:
            self.first_name = " ".join(self.first_name.split())

        if self.last_name:
            self.last_name = " ".join(self.last_name.split())

        # 2. Identificación personal (DNI y CUIL/CUIT)
        if self.dni:
            # Extraer solo dígitos
            dni_limpio = re.sub(r"\D", "", str(self.dni))
            self.dni = dni_limpio if dni_limpio else None
        else:
            self.dni = None

        if self.cuil_cuit:
            # Extraer solo dígitos y formatear XX-XXXXXXXX-X si tiene 11 dígitos
            cuil_digits = re.sub(r"\D", "", str(self.cuil_cuit))
            if len(cuil_digits) == 11:
                self.cuil_cuit = f"{cuil_digits[:2]}-{cuil_digits[2:10]}-{cuil_digits[10]}"
            elif cuil_digits:
                self.cuil_cuit = cuil_digits
            else:
                self.cuil_cuit = None
        else:
            self.cuil_cuit = None

        if self.lugar_nacimiento:
            self.lugar_nacimiento = " ".join(self.lugar_nacimiento.split())

        if self.nacionalidad:
            self.nacionalidad = str(self.nacionalidad).strip().upper()

        # 3. Domicilio real
        if self.domicilio_real_calle:
            self.domicilio_real_calle = " ".join(self.domicilio_real_calle.split())

        if self.domicilio_real_numero:
            self.domicilio_real_numero = " ".join(self.domicilio_real_numero.split()).upper()

        if self.domicilio_real_piso_depto:
            self.domicilio_real_piso_depto = " ".join(self.domicilio_real_piso_depto.split()).upper()

        if self.domicilio_real_localidad:
            self.domicilio_real_localidad = " ".join(self.domicilio_real_localidad.split())

        if self.domicilio_real_provincia:
            self.domicilio_real_provincia = " ".join(self.domicilio_real_provincia.split())

        if self.domicilio_real_pais:
            self.domicilio_real_pais = str(self.domicilio_real_pais).strip().upper()

        if self.domicilio_real_cp:
            self.domicilio_real_cp = " ".join(self.domicilio_real_cp.split()).upper()

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)


class MembresiaComision(models.Model):
    class Comision(models.TextChoices):
        DIRECTIVA = "DIRECTIVA", "Comisión Directiva"
        REVISORA_CUENTAS = "REVISORA_CUENTAS", "Comisión Revisora de Cuentas"

    class Cargo(models.TextChoices):
        # Comisión Directiva
        PRESIDENTE = "PRESIDENTE", "Presidente/a"
        VICEPRESIDENTE = "VICEPRESIDENTE", "Vicepresidente/a"
        SECRETARIO = "SECRETARIO", "Secretario/a"
        TESORERO = "TESORERO", "Tesorero/a"
        VOCAL_TITULAR_1 = "VOCAL_TITULAR_1", "Vocal Titular 1"
        VOCAL_TITULAR_2 = "VOCAL_TITULAR_2", "Vocal Titular 2"
        VOCAL_TITULAR_3 = "VOCAL_TITULAR_3", "Vocal Titular 3"
        VOCAL_SUPLENTE_1 = "VOCAL_SUPLENTE_1", "Vocal Suplente 1"
        VOCAL_SUPLENTE_2 = "VOCAL_SUPLENTE_2", "Vocal Suplente 2"
        # Comisión Revisora de Cuentas
        REVISOR_TITULAR_1 = "REVISOR_TITULAR_1", "Revisor/a de Cuentas Titular 1"
        REVISOR_TITULAR_2 = "REVISOR_TITULAR_2", "Revisor/a de Cuentas Titular 2"
        REVISOR_SUPLENTE_1 = "REVISOR_SUPLENTE_1", "Revisor/a de Cuentas Suplente 1"
        REVISOR_SUPLENTE_2 = "REVISOR_SUPLENTE_2", "Revisor/a de Cuentas Suplente 2"

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cargos",
        verbose_name="Usuario",
    )
    comision = models.CharField(
        max_length=20,
        choices=Comision.choices,
        verbose_name="Comisión",
    )
    cargo = models.CharField(
        max_length=30,
        choices=Cargo.choices,
        verbose_name="Cargo dentro de la comisión",
    )
    fecha_desde = models.DateField(
        verbose_name="Fecha de asunción",
    )
    fecha_hasta = models.DateField(
        verbose_name="Fecha de finalización de mandato",
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membresias_creadas",
        verbose_name="Creado por",
    )
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membresias_modificadas",
        verbose_name="Modificado por",
    )

    class Meta:
        db_table = "membresias_comision"
        verbose_name = "Membresía en Comisión"
        verbose_name_plural = "Membresías en Comisión"
        ordering = ["-fecha_desde", "cargo"]

    def __str__(self):
        return f"{self.get_cargo_display()} - {self.usuario.get_full_name() or self.usuario.username} ({self.fecha_desde.year})"

    def clean(self):
        super().clean()
        self.normalizar_datos()
        self.validar_datos()

    def validar_datos(self):
        """
        Valida coherencia de fechas y correspondencia entre comisión y cargo.
        """
        errores = {}

        # 1. Rango de fechas
        if self.fecha_desde and self.fecha_hasta:
            if self.fecha_hasta < self.fecha_desde:
                errores["fecha_hasta"] = "La fecha de finalización no puede ser anterior a la fecha de asunción."

        # 2. Coherencia entre Comisión y Cargo
        cargos_directiva = [
            self.Cargo.PRESIDENTE,
            self.Cargo.VICEPRESIDENTE,
            self.Cargo.SECRETARIO,
            self.Cargo.TESORERO,
            self.Cargo.VOCAL_TITULAR_1,
            self.Cargo.VOCAL_TITULAR_2,
            self.Cargo.VOCAL_TITULAR_3,
            self.Cargo.VOCAL_SUPLENTE_1,
            self.Cargo.VOCAL_SUPLENTE_2,
        ]

        cargos_revisora = [
            self.Cargo.REVISOR_TITULAR_1,
            self.Cargo.REVISOR_TITULAR_2,
            self.Cargo.REVISOR_SUPLENTE_1,
            self.Cargo.REVISOR_SUPLENTE_2,
        ]

        if self.comision == self.Comision.DIRECTIVA:
            if self.cargo and self.cargo not in cargos_directiva:
                errores["cargo"] = "El cargo seleccionado no corresponde a la Comisión Directiva."
        elif self.comision == self.Comision.REVISORA_CUENTAS:
            if self.cargo and self.cargo not in cargos_revisora:
                errores["cargo"] = "El cargo seleccionado no corresponde a la Comisión Revisora de Cuentas."

        if errores:
            raise ValidationError(errores)

    def normalizar_datos(self):
        """
        Normaliza campos de selección y texto antes de persistir.
        """
        if self.comision:
            self.comision = str(self.comision).strip().upper()
        if self.cargo:
            self.cargo = str(self.cargo).strip().upper()

    def save(self, *args, **kwargs):
        self.normalizar_datos()
        super().save(*args, **kwargs)

    @property
    def es_vigente(self):
        from django.utils import timezone
        hoy = timezone.now().date()
        if self.fecha_desde > hoy:
            return False
        return self.fecha_hasta is None or self.fecha_hasta > hoy
