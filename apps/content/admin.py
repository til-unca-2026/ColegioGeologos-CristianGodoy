from django.contrib import admin
from .models import Contenido, ImagenContenido, DetalleEvento


class ImagenContenidoInline(admin.TabularInline):
    model = ImagenContenido
    extra = 1
    fields = ("imagen", "texto_alt", "epigrafe", "orden", "es_portada")


class DetalleEventoInline(admin.StackedInline):
    model = DetalleEvento
    extra = 0
    can_delete = True
    fields = ("inicio", "fin", "lugar", "modalidad", "link_inscripcion", "cupo")


@admin.register(Contenido)
class ContenidoAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "tipo",
        "estado_publicacion",
        "visibilidad",
        "destacado",
        "fecha_publicacion",
        "esta_publicado_status",
        "creado_por",
    )
    list_filter = (
        "tipo",
        "estado_publicacion",
        "visibilidad",
        "destacado",
        "fecha_publicacion",
    )
    search_fields = ("titulo", "resumen", "cuerpo", "slug")
    prepopulated_fields = {"slug": ("titulo",)}
    date_hierarchy = "fecha_publicacion"
    readonly_fields = ("fecha_creacion", "fecha_modificacion", "creado_por", "modificado_por")
    inlines = [ImagenContenidoInline, DetalleEventoInline]

    fieldsets = (
        (
            "Información Principal",
            {
                "fields": (
                    "tipo",
                    "titulo",
                    "slug",
                    "resumen",
                    "cuerpo",
                )
            },
        ),
        (
            "Publicación y Visibilidad",
            {
                "fields": (
                    "estado_publicacion",
                    "fecha_publicacion",
                    "visibilidad",
                    "destacado",
                )
            },
        ),
        (
            "Auditoría",
            {
                "classes": ("collapse",),
                "fields": (
                    "creado_por",
                    "modificado_por",
                    "fecha_creacion",
                    "fecha_modificacion",
                ),
            },
        ),
    )

    @admin.display(description="Publicado", boolean=True)
    def esta_publicado_status(self, obj):
        return obj.esta_publicado

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ImagenContenido)
class ImagenContenidoAdmin(admin.ModelAdmin):
    list_display = ("id", "contenido", "orden", "es_portada", "texto_alt")
    list_filter = ("es_portada", "contenido__tipo")
    search_fields = ("contenido__titulo", "texto_alt", "epigrafe")


@admin.register(DetalleEvento)
class DetalleEventoAdmin(admin.ModelAdmin):
    list_display = ("contenido", "inicio", "fin", "modalidad", "lugar", "cupo")
    list_filter = ("modalidad", "inicio")
    search_fields = ("contenido__titulo", "lugar")

