from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
)
from django.db.models import Case, When, Value, IntegerField, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import (
    AdminUserCreateForm,
    AdminUserEditForm,
    CustomAuthenticationForm,
    MembresiaComisionForm,
    UserProfileUpdateForm,
)
from .models import MembresiaComision


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Pestaña activa por query param (?tab=...)
        current_tab = self.request.GET.get("tab", "perfil")

        # Formulario de autogestión de perfil si no se pasó en POST con error
        if "profile_form" not in context:
            context["profile_form"] = UserProfileUpdateForm(instance=user)

        # Capacidad de gestión administrativa basada en permisos Django
        can_manage_users = user.has_perm("accounts.view_user") or user.has_perm("accounts.add_user")
        can_manage_matriculados = (
            user.has_perm("directory.view_matriculado")
            or user.has_perm("directory.add_matriculado")
            or user.has_perm("directory.change_matriculado")
            or user.is_superuser
        )
        can_manage_comision = (
            user.has_perm("accounts.view_membresiacomision")
            or user.has_perm("accounts.add_membresiacomision")
            or user.has_perm("accounts.change_membresiacomision")
            or user.is_superuser
        )

        # Consulta de datos matriculares propios si el usuario está matriculado
        from apps.directory.models import Matriculado
        mi_matricula = None
        mis_titulos = []
        mi_estado_actual = None
        try:
            mi_matricula = (
                Matriculado.objects.select_related("usuario")
                .prefetch_related("especialidades", "titulos__emitido_por", "estados")
                .get(usuario=user)
            )
            mis_titulos = mi_matricula.titulos.all()
            mi_estado_actual = mi_matricula.estado_actual
        except Matriculado.DoesNotExist:
            pass

        context.update({
            "current_tab": current_tab,
            "can_manage_users": can_manage_users,
            "can_manage_matriculados": can_manage_matriculados,
            "can_manage_comision": can_manage_comision,
            "mi_matricula": mi_matricula,
            "mis_titulos": mis_titulos,
            "mi_estado_actual": mi_estado_actual,
        })

        if can_manage_matriculados:
            from apps.directory.models import Matriculado, Especialidad, Universidad
            from apps.directory.forms import EspecialidadForm, UniversidadForm
            search_mat = self.request.GET.get("q_mat", "").strip()
            especialidad_filtro = self.request.GET.get("especialidad", "")
            
            mat_qs = (
                Matriculado.objects.select_related("usuario")
                .prefetch_related("especialidades", "estados", "titulos")
                .order_by("-fecha_matriculacion")
            )
            if search_mat:
                from django.db.models import Q
                mat_qs = mat_qs.filter(
                    Q(numero_matricula__icontains=search_mat)
                    | Q(usuario__first_name__icontains=search_mat)
                    | Q(usuario__last_name__icontains=search_mat)
                    | Q(usuario__dni__icontains=search_mat)
                    | Q(usuario__email__icontains=search_mat)
                )
            if especialidad_filtro:
                mat_qs = mat_qs.filter(especialidades__id=especialidad_filtro)

            # Catálogos maestros para administración y corrección de tipeo
            search_esp = self.request.GET.get("q_esp", "").strip()
            esp_qs = Especialidad.objects.all().order_by("nombre")
            if search_esp:
                esp_qs = esp_qs.filter(nombre__icontains=search_esp)

            search_univ = self.request.GET.get("q_univ", "").strip()
            univ_qs = Universidad.objects.all().order_by("nombre")
            if search_univ:
                univ_qs = univ_qs.filter(
                    Q(nombre__icontains=search_univ) | Q(sigla__icontains=search_univ)
                )

            context["matriculados_list"] = mat_qs
            context["search_mat"] = search_mat
            context["especialidad_filtro"] = especialidad_filtro
            context["especialidades_disponibles"] = Especialidad.objects.all().order_by("nombre")
            context["especialidades_list"] = esp_qs
            context["search_esp"] = search_esp
            context["universidades_list"] = univ_qs
            context["search_univ"] = search_univ
            context["especialidad_form"] = EspecialidadForm()
            context["universidad_form"] = UniversidadForm()

        if can_manage_users:
            User = get_user_model()
            context["users_list"] = User.objects.all().prefetch_related("groups").order_by("-date_joined")

        if can_manage_comision:
            comision_filtro = self.request.GET.get("comision", "")
            estado_filtro = self.request.GET.get("estado", "")

            qs = MembresiaComision.objects.select_related("usuario").order_by("-fecha_desde", "cargo")
            if comision_filtro:
                qs = qs.filter(comision=comision_filtro)
            if estado_filtro == "vigente":
                qs = qs.filter(fecha_hasta__isnull=True)
            elif estado_filtro == "concluido":
                qs = qs.filter(fecha_hasta__isnull=False)

            context["comision_list"] = qs
            context["comision_filtro"] = comision_filtro
            context["estado_filtro"] = estado_filtro
            context["comisiones_disponibles"] = MembresiaComision.Comision.choices

        return context

    def post(self, request, *args, **kwargs):
        """
        Procesa la actualización de los datos de perfil/autogestión del propio usuario.
        """
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.modificado_por = request.user
            user.save()
            messages.success(request, "Tus datos de perfil y preferencias han sido actualizados exitosamente.")
            return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=perfil")
        
        # Si hubo errores de validación, re-renderizar manteniendo la solapa perfil
        messages.error(request, "Por favor revise los errores en el formulario de perfil.")
        return self.render_to_response(
            self.get_context_data(profile_form=form, current_tab="perfil")
        )


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "accounts.add_user"
    form_class = AdminUserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:dashboard")

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_usuarios"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.creado_por = self.request.user
        user.save()
        form.save_m2m()
        messages.success(
            self.request,
            f"El usuario '{user.username}' fue creado correctamente con el grupo asignado.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        context["title"] = "Crear nuevo usuario"
        return context


class UserEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "accounts.change_user"
    model = get_user_model()
    form_class = AdminUserEditForm
    template_name = "accounts/user_form.html"

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_usuarios"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.modificado_por = self.request.user
        user.save()
        form.save_m2m()
        messages.success(
            self.request,
            f"El usuario '{user.username}' fue actualizado correctamente.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context["title"] = f"Editar usuario: {self.object.username}"
        return context


class MembresiaComisionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "accounts.add_membresiacomision"
    model = MembresiaComision
    form_class = MembresiaComisionForm
    template_name = "accounts/comision_form.html"

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_comision"

    def form_valid(self, form):
        membresia = form.save(commit=False)
        membresia.creado_por = self.request.user
        membresia.save()
        messages.success(
            self.request,
            f"El cargo '{membresia.get_cargo_display()}' fue asignado a '{membresia.usuario.get_full_name() or membresia.usuario.username}'.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        context["title"] = "Asignar cargo o designación"
        return context


class MembresiaComisionEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "accounts.change_membresiacomision"
    model = MembresiaComision
    form_class = MembresiaComisionForm
    template_name = "accounts/comision_form.html"

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=admin_comision"

    def form_valid(self, form):
        membresia = form.save(commit=False)
        membresia.modificado_por = self.request.user
        membresia.save()
        messages.success(
            self.request,
            f"Se actualizaron los datos del cargo para '{membresia.usuario.get_full_name() or membresia.usuario.username}'.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context["title"] = f"Editar cargo: {self.object.get_cargo_display()}"
        return context


class MembresiaComisionFinalizarView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Acción directa para dar por concluido un mandato asignando la fecha de hoy como fecha_hasta.
    """
    permission_required = "accounts.change_membresiacomision"

    def post(self, request, pk, *args, **kwargs):
        membresia = get_object_or_404(MembresiaComision, pk=pk)
        hoy = timezone.now().date()
        membresia.fecha_hasta = hoy
        membresia.modificado_por = request.user
        membresia.save()
        messages.success(
            request,
            f"Se finalizó el mandato de '{membresia.get_cargo_display()}' para '{membresia.usuario.get_full_name() or membresia.usuario.username}'.",
        )
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_comision")


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        # Si el error es por matrícula inhabilitada, form.non_field_errors() ya tiene el mensaje explícito.
        # Solo mostramos el genérico si no hay un error específico más descriptivo.
        errors = form.non_field_errors()
        if errors:
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


class AccountLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        messages.success(request, "Cerraste sesión correctamente.")
        return super().post(request, *args, **kwargs)


class AccountPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, self.request.user)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        messages.success(self.request, "La contraseña se cambió correctamente.")
        return response


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.user.must_change_password:
            self.user.must_change_password = False
            self.user.save(update_fields=["must_change_password"])
        return response


class AutoridadesView(ListView):
    template_name = "accounts/autoridades.html"
    context_object_name = "autoridades"

    def get_queryset(self):
        hoy = timezone.now().date()
        cargo_order = [
            MembresiaComision.Cargo.PRESIDENTE,
            MembresiaComision.Cargo.VICEPRESIDENTE,
            MembresiaComision.Cargo.SECRETARIO,
            MembresiaComision.Cargo.PROSECRETARIO,
            MembresiaComision.Cargo.TESORERO,
            MembresiaComision.Cargo.PROTESORERO,
            MembresiaComision.Cargo.VOCAL_TITULAR,
            MembresiaComision.Cargo.VOCAL_SUPLENTE,
        ]
        whens = [When(cargo=cargo, then=Value(i)) for i, cargo in enumerate(cargo_order)]

        return (
            MembresiaComision.objects.filter(
                comision=MembresiaComision.Comision.DIRECTIVA,
                fecha_desde__lte=hoy,
            )
            .filter(Q(fecha_hasta__isnull=True) | Q(fecha_hasta__gte=hoy))
            .select_related("usuario")
            .annotate(cargo_priority=Case(*whens, default=Value(99), output_field=IntegerField()))
            .order_by("cargo_priority", "-fecha_desde", "usuario__last_name", "usuario__first_name")
        )
