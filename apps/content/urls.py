from django.urls import path
from .views import (
    NovedadesListView,
    NovedadDetailView,
    ContenidoCreateView,
    ContenidoUpdateView,
    ContenidoDeleteView,
    ContenidoToggleEstadoView,
    ImagenContenidoDeleteView,
)

app_name = "content"

urlpatterns = [
    # Listado público y detalle
    path("", NovedadesListView.as_view(), name="novedades_list"),
    path("detalle/<slug:slug>/", NovedadDetailView.as_view(), name="novedad_detail"),
    path("detalle-id/<int:pk>/", NovedadDetailView.as_view(), name="novedad_detail_id"),

    # Gestión (Colaboradores / Administradores)
    path("create/", ContenidoCreateView.as_view(), name="contenido_create"),
    path("<int:pk>/edit/", ContenidoUpdateView.as_view(), name="contenido_edit"),
    path("<int:pk>/delete/", ContenidoDeleteView.as_view(), name="contenido_delete"),
    path("<int:pk>/toggle-estado/", ContenidoToggleEstadoView.as_view(), name="contenido_toggle_estado"),
    path("imagen/<int:pk>/delete/", ImagenContenidoDeleteView.as_view(), name="imagen_delete"),
]
