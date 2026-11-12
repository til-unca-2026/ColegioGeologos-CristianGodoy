from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "titulo",
        "categoria",
        "fecha_documento",
        "vigente",
        "visibilidad",
        "creado_por",
        "fecha_creacion",
    )
    list_filter = (
        "categoria",
        "vigente",
        "visibilidad",
        "fecha_documento",
    )
    search_fields = (
        "titulo",
        "numero",
        "descripcion",
    )
    readonly_fields = (
        "fecha_creacion",
        "fecha_modificacion",
        "creado_por",
        "modificado_por",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)

