from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import DocumentoForm
from .models import Documento


class DocumentoListView(ListView):
    """
    Vista pública e institucional para consulta y descarga de documentos oficiales.
    Aplica las reglas de visibilidad (docs/11):
    - Visitante anónimo: solo PUBLICO.
    - Usuario autenticado / matriculado: PUBLICO y MATRICULADOS.
    - Staff / Colaborador / Administrador: PUBLICO, MATRICULADOS e INTERNO.
    """
    model = Documento
    template_name = "documents/documento_list.html"
    context_object_name = "documentos"
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        qs = Documento.objects.select_related("creado_por")

        # Reglas de visibilidad
        es_staff = user.is_authenticated and (
            user.is_superuser
            or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
            or user.has_perm("documents.change_documento")
        )

        if not es_staff:
            if user.is_authenticated:
                qs = qs.filter(visibilidad__in=[Documento.Visibilidad.PUBLICO, Documento.Visibilidad.MATRICULADOS])
            else:
                qs = qs.filter(visibilidad=Documento.Visibilidad.PUBLICO)

        # Filtro por categoría
        categoria = self.request.GET.get("categoria", "").strip()
        if categoria and categoria in Documento.Categoria.values:
            qs = qs.filter(categoria=categoria)

        # Filtro por vigencia (por defecto solo vigentes, con opción de 'todos' o 'no_vigentes')
        vigencia = self.request.GET.get("vigencia", "vigentes").strip()
        if vigencia == "vigentes":
            qs = qs.filter(vigente=True)
        elif vigencia == "no_vigentes":
            qs = qs.filter(vigente=False)
        # Si vigencia == "todos", no se aplica filtro de vigente

        # Búsqueda libre
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(titulo__icontains=q)
                | Q(numero__icontains=q)
                | Q(descripcion__icontains=q)
            )

        return qs.order_by("-fecha_documento", "-fecha_creacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categoria_actual"] = self.request.GET.get("categoria", "")
        context["vigencia_actual"] = self.request.GET.get("vigencia", "vigentes")
        context["q"] = self.request.GET.get("q", "")
        context["categorias_disponibles"] = Documento.Categoria.choices
        context["total_documentos"] = self.get_queryset().count()
        return context


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Permite acceso a administradores o superusuarios según RF-28 y docs/11.
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.groups.filter(name="Administradores").exists()
            or user.has_perm("documents.add_documento")
            or user.has_perm("documents.change_documento")
        )

    def handle_no_permission(self):
        messages.error(self.request, "Solo los administradores pueden gestionar documentos institucionales.")
        return redirect("accounts:dashboard")


class DocumentoCreateView(AdminRequiredMixin, CreateView):
    model = Documento
    form_class = DocumentoForm
    template_name = "documents/documento_form.html"
    success_url = reverse_lazy("accounts:dashboard")

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_documentos"

    def form_valid(self, form):
        documento = form.save(commit=False)
        documento.creado_por = self.request.user
        documento.save()
        messages.success(self.request, f"Documento «{documento.numero} - {documento.titulo}» creado con éxito.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context


class DocumentoUpdateView(AdminRequiredMixin, UpdateView):
    model = Documento
    form_class = DocumentoForm
    template_name = "documents/documento_form.html"

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_documentos"

    def form_valid(self, form):
        documento = form.save(commit=False)
        documento.modificado_por = self.request.user
        documento.save()
        messages.success(self.request, f"Documento «{documento.numero} - {documento.titulo}» actualizado con éxito.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        return context


class DocumentoDeleteView(AdminRequiredMixin, DeleteView):
    model = Documento

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_documentos"

    def delete(self, request, *args, **kwargs):
        documento = self.get_object()
        titulo = f"{documento.numero} - {documento.titulo}"
        documento.delete()
        messages.success(request, f"El documento «{titulo}» fue eliminado correctamente.")
        return redirect(self.get_success_url())


class DocumentoToggleVigenteView(AdminRequiredMixin, View):
    """
    Alterna rápidamente el estado vigente/no vigente desde la tabla del dashboard.
    """
    def post(self, request, pk, *args, **kwargs):
        documento = get_object_or_404(Documento, pk=pk)
        documento.vigente = not documento.vigente
        documento.modificado_por = request.user
        documento.save(update_fields=["vigente", "modificado_por"])
        estado_str = "vigente" if documento.vigente else "no vigente"
        messages.success(request, f"El documento «{documento.numero}» ahora figura como {estado_str}.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_documentos")

