# core/storage.py
import mimetypes
from threading import Lock
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.deconstruct import deconstructible
from supabase import Client, create_client


_supabase_client: Client | None = None
_supabase_client_lock = Lock()


def get_supabase_client() -> Client:
    global _supabase_client

    if _supabase_client is None:
        with _supabase_client_lock:
            if _supabase_client is None:
                url = settings.SUPABASE_URL
                key = settings.SUPABASE_KEY
                if not url or not key:
                    raise ImproperlyConfigured(
                        "SUPABASE_URL and SUPABASE_KEY must be configured to use Supabase Storage."
                    )
                _supabase_client = create_client(url, key)

    return _supabase_client


@deconstructible
class SupabaseStorage(Storage):
    """
    Storage backend personalizado para Django que sube y recupera
    archivos directamente desde Supabase Storage.
    """

    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'colegio-media')

    @property
    def client(self):
        return get_supabase_client()

    def _save(self, name, content):
        # Normalizar barras a estilo Unix para storage
        clean_name = name.replace('\\', '/')
        
        # Leer el contenido binario del archivo
        content.seek(0)
        file_bytes = content.read()
        
        # Obtener el tipo de contenido (mimetype)
        content_type, _ = mimetypes.guess_type(clean_name)
        file_options = {"content-type": content_type or "application/octet-stream", "upsert": "true"}

        # Subir a Supabase Storage
        self.client.storage.from_(self.bucket_name).upload(
            path=clean_name,
            file=file_bytes,
            file_options=file_options
        )
        return clean_name

    def _open(self, name, mode='rb'):
        clean_name = name.replace('\\', '/')
        response = self.client.storage.from_(self.bucket_name).download(clean_name)
        return ContentFile(response)

    def exists(self, name):
        # Con upsert=true permitimos sobreescrituras seguras generadas por Django
        return False

    def url(self, name):
        clean_name = name.replace('\\', '/')
        res = self.client.storage.from_(self.bucket_name).get_public_url(clean_name)
        # Compatible según versión de supabase-py (puede devolver string o dict)
        if isinstance(res, dict):
            return res.get('publicUrl', '')
        return res

    def delete(self, name):
        clean_name = name.replace('\\', '/')
        self.client.storage.from_(self.bucket_name).remove([clean_name])
