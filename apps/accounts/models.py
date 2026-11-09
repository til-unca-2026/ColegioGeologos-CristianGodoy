from django.db import models
from django.contrib.auth.models import AbstractUser
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
        default="AR",
        blank=True,
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
        default="AR",
        blank=True,
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


class MembresiaComision(models.Model):
    class Comision(models.TextChoices):
        DIRECTIVA = "DIRECTIVA", "Comisión Directiva"

    class Cargo(models.TextChoices):
        PRESIDENTE = "PRESIDENTE", "Presidente"
        VICEPRESIDENTE = "VICEPRESIDENTE", "Vicepresidente"
        SECRETARIO = "SECRETARIO", "Secretario"
        PROSECRETARIO = "PROSECRETARIO", "Prosecretario"
        TESORERO = "TESORERO", "Tesorero"
        PROTESORERO = "PROTESORERO", "Protesorero"
        VOCAL_TITULAR = "VOCAL_TITULAR", "Vocal Titular"
        VOCAL_SUPLENTE = "VOCAL_SUPLENTE", "Vocal Suplente"

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cargos",
        verbose_name="Usuario",
    )
    comision = models.CharField(
        max_length=20,
        choices=Comision.choices,
        default=Comision.DIRECTIVA,
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
        null=True,
        blank=True,
        verbose_name="Fecha de finalización de mandato",
        help_text="Dejar vacío si el cargo continúa vigente.",
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

    @property
    def es_vigente(self):
        from django.utils import timezone
        hoy = timezone.now().date()
        if self.fecha_desde > hoy:
            return False
        return self.fecha_hasta is None or self.fecha_hasta >= hoy
