from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView


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
