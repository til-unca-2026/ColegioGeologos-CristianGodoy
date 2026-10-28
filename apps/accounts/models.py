from django.db import models
from django.contrib.auth.models import AbstractUser
from core.storage import SupabaseStorage

class User(AbstractUser):
    class Position(models.TextChoices):
        PRESIDENTE = 'presidente', 'Presidente'
        VICEPRESIDENTE = 'vicepresidente', 'Vicepresidente'
        SECRETARIO = 'secretario', 'Secretario'
        PROSECRETARIO = 'prosecretario', 'Prosecretario'
        TESORERO = 'tesorero', 'Tesorero'
        PROTESORERO = 'protesorero', 'Protesorero'
        VOCAL_TITULAR = 'vocal_titular', 'Vocal Titular'
        VOCAL_SUPLENTE = 'vocal_suplente', 'Vocal Suplente'

    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    position = models.CharField(
        max_length=20,
        choices=Position.choices,
        blank=True,
        null=True,
        verbose_name="Cargo en la comisión"
    )
    profile_picture = models.ImageField(
        upload_to='profiles/',
        storage=SupabaseStorage(),
        blank=True,
        null=True,
        verbose_name="Foto de perfil"
    )
    must_change_password = models.BooleanField(
        default=False,
        verbose_name="Debe cambiar la contraseña",
    )
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
