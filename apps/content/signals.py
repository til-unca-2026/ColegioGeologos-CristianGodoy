from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import ImagenContenido


@receiver(post_delete, sender=ImagenContenido)
def delete_image_on_imagencontenido_delete(sender, instance, **kwargs):
    """
    Elimina el archivo físico en Supabase Storage cuando la instancia de ImagenContenido
    es eliminada (ya sea de forma individual o en cascada al borrar el Contenido).
    """
    if instance.imagen:
        instance.imagen.delete(save=False)


@receiver(pre_save, sender=ImagenContenido)
def delete_old_image_on_change(sender, instance, **kwargs):
    """
    Elimina la imagen anterior en Supabase Storage si se reemplaza por un nuevo archivo.
    """
    if not instance.pk:
        return  # Instancia nueva, no hay archivo previo

    try:
        old_instance = ImagenContenido.objects.get(pk=instance.pk)
    except ImagenContenido.DoesNotExist:
        return

    # Si tenía archivo previo y cambió por otro o se vació
    if old_instance.imagen and old_instance.imagen != instance.imagen:
        old_instance.imagen.delete(save=False)

