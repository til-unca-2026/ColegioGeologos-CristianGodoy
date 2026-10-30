from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Pestaña activa por query param (?tab=...)
        current_tab = self.request.GET.get("tab", "perfil")

        # Capacidad de gestión administrativa basada en permisos Django
        can_manage_users = user.has_perm("accounts.view_user") or user.has_perm("accounts.add_user")

        context.update({
            "current_tab": current_tab,
            "can_manage_users": can_manage_users,
        })

        if can_manage_users:
            User = get_user_model()
            context["users_list"] = User.objects.all().order_by("-date_joined")[:15]

        return context


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        if form.non_field_errors():
            messages.error(self.request, "Usuario o contraseña incorrectos.")
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
