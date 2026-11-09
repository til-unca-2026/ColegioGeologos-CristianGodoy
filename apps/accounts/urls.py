from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import (
    AccountLoginView,
    AccountLogoutView,
    AccountPasswordChangeView,
    AccountPasswordResetConfirmView,
    DashboardView,
    MembresiaComisionCreateView,
    MembresiaComisionEditView,
    MembresiaComisionFinalizarView,
    UserCreateView,
    UserEditView,
)

app_name = "accounts"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard/users/create/", UserCreateView.as_view(), name="user_create"),
    path("dashboard/users/<int:pk>/edit/", UserEditView.as_view(), name="user_edit"),
    path("dashboard/comision/create/", MembresiaComisionCreateView.as_view(), name="comision_create"),
    path("dashboard/comision/<int:pk>/edit/", MembresiaComisionEditView.as_view(), name="comision_edit"),
    path("dashboard/comision/<int:pk>/finalizar/", MembresiaComisionFinalizarView.as_view(), name="comision_finalizar"),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
    path("password/change/", AccountPasswordChangeView.as_view(), name="password_change"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        AccountPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
