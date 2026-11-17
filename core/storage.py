# core/storage.py
import mimetypes
import os
import re
import unicodedata
from threading import Lock
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.deconstruct import deconstructible
from django.utils.text import get_valid_filename
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

    def get_valid_name(self, name):
        """
        Normaliza el nombre del archivo para que sea compatible con Supabase Storage (S3 / REST key).
        Elimina tildes, caracteres especiales, espacios y asegura compatibilidad ASCII.
        """
        name = str(name).replace('\\', '/')
        dirname, filename = os.path.split(name)
        
        # Separar nombre base y extensión
        base, ext = os.path.splitext(filename)
        # Normalizar caracteres con acentos/tildes a ASCII (ej: í -> i, ñ -> n)
        normalized_base = unicodedata.normalize('NFKD', base).encode('ascii', 'ignore').decode('ascii')
        # Reemplazar cualquier caracter no alfanumérico (excepto guiones o guiones bajos) por guion bajo
        clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', normalized_base)
        # Limpiar guiones bajos duplicados
        clean_base = re.sub(r'_+', '_', clean_base).strip('._')
        
        if not clean_base:
            clean_base = "archivo"

        clean_ext = ext.lower().strip()
        clean_filename = f"{clean_base}{clean_ext}"
        
        if dirname:
            return f"{dirname.rstrip('/')}/{clean_filename}"
        return clean_filename

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
