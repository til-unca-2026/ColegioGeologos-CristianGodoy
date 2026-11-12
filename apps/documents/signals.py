from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Documento


@receiver(post_delete, sender=Documento)
def delete_file_on_documento_delete(sender, instance, **kwargs):
    """
    Elimina el archivo PDF físico en Supabase Storage cuando el Documento es eliminado.
    """
    if instance.archivo_almacenado:
        instance.archivo_almacenado.delete(save=False)


@receiver(pre_save, sender=Documento)
def delete_old_file_on_documento_change(sender, instance, **kwargs):
    """
    Elimina el archivo PDF anterior en Supabase Storage si se reemplaza por uno nuevo.
    """
    if not instance.pk:
        return

    try:
        old_instance = Documento.objects.get(pk=instance.pk)
    except Documento.DoesNotExist:
        return

    if old_instance.archivo_almacenado and old_instance.archivo_almacenado != instance.archivo_almacenado:
        old_instance.archivo_almacenado.delete(save=False)

