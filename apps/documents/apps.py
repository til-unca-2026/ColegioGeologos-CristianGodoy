from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Documentos Institucionales'

    def ready(self):
        import apps.documents.signals  # noqa: F401
