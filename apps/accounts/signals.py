from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import User


@receiver(post_delete, sender=User)
def delete_profile_picture_on_user_delete(sender, instance, **kwargs):
    """
    Elimina la foto de perfil en Supabase Storage cuando el usuario es eliminado.
    """
    if instance.profile_picture:
        # El método delete(save=False) del FieldFile invoca el delete() de SupabaseStorage
        instance.profile_picture.delete(save=False)


@receiver(pre_save, sender=User)
def delete_old_profile_picture_on_change(sender, instance, **kwargs):
    """
    Elimina la foto vieja en Supabase Storage si el usuario actualiza su foto de perfil.
    """
    if not instance.pk:
        return  # Es un usuario nuevo, no hay foto previa que borrar

    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # Si tenía foto previa y ahora cambió por otra (o se borró)
    if old_user.profile_picture and old_user.profile_picture != instance.profile_picture:
        old_user.profile_picture.delete(save=False)
