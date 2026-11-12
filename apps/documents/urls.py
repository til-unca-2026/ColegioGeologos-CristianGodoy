from django.urls import path
from .views import (
    DocumentoListView,
    DocumentoCreateView,
    DocumentoUpdateView,
    DocumentoDeleteView,
    DocumentoToggleVigenteView,
)

app_name = "documents"

urlpatterns = [
    path("", DocumentoListView.as_view(), name="documento_list"),
    path("create/", DocumentoCreateView.as_view(), name="documento_create"),
    path("<int:pk>/edit/", DocumentoUpdateView.as_view(), name="documento_edit"),
    path("<int:pk>/delete/", DocumentoDeleteView.as_view(), name="documento_delete"),
    path("<int:pk>/toggle-vigente/", DocumentoToggleVigenteView.as_view(), name="documento_toggle_vigente"),
]

