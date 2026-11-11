from django.urls import path
from .views import (
    MatriculadoCreateView,
    MatriculadoUpdateView,
    MatriculadoDetailView,
    TituloCreateView,
    TituloUpdateView,
    HistorialEstadoCreateView,
    HistorialEstadoUpdateView,
    AntecedenteDisciplinarioCreateView,
    AntecedenteDisciplinarioUpdateView,
    EspecialidadCreateView,
    EspecialidadUpdateView,
    EspecialidadCreateAjaxView,
    UniversidadCreateView,
    UniversidadUpdateView,
    UniversidadCreateAjaxView,
    DirectorioPublicListView,
    DirectorioPublicDetailView,
)

app_name = "directory"

urlpatterns = [
    # Directorio Público (Público general)
    path("", DirectorioPublicListView.as_view(), name="public_list"),
    path("profesional/<int:pk>/", DirectorioPublicDetailView.as_view(), name="public_detail"),

    # Gestión de Matriculados (Administración / Ficha interna)
    path("matriculados/create/", MatriculadoCreateView.as_view(), name="matriculado_create"),
    path("matriculados/<int:pk>/", MatriculadoDetailView.as_view(), name="matriculado_detail"),
    path("matriculados/<int:pk>/edit/", MatriculadoUpdateView.as_view(), name="matriculado_edit"),

    # Sub-entidades del profesional (Creación y Edición)
    path("matriculados/<int:matriculado_id>/titulos/create/", TituloCreateView.as_view(), name="titulo_create"),
    path("titulos/<int:pk>/edit/", TituloUpdateView.as_view(), name="titulo_edit"),

    path("matriculados/<int:matriculado_id>/estados/create/", HistorialEstadoCreateView.as_view(), name="estado_create"),
    path("estados/<int:pk>/edit/", HistorialEstadoUpdateView.as_view(), name="estado_edit"),

    path("matriculados/<int:matriculado_id>/antecedentes/create/", AntecedenteDisciplinarioCreateView.as_view(), name="antecedente_create"),
    path("antecedentes/<int:pk>/edit/", AntecedenteDisciplinarioUpdateView.as_view(), name="antecedente_edit"),

    # Especialidades y Universidades (Gestión administrativa y AJAX)
    path("especialidades/create/", EspecialidadCreateView.as_view(), name="especialidad_create"),
    path("especialidades/<int:pk>/edit/", EspecialidadUpdateView.as_view(), name="especialidad_edit"),
    path("especialidades/ajax/create/", EspecialidadCreateAjaxView.as_view(), name="especialidad_create_ajax"),

    path("universidades/create/", UniversidadCreateView.as_view(), name="universidad_create"),
    path("universidades/<int:pk>/edit/", UniversidadUpdateView.as_view(), name="universidad_edit"),
    path("universidades/ajax/create/", UniversidadCreateAjaxView.as_view(), name="universidad_create_ajax"),
]
