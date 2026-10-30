from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class AuthenticationViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="geologo",
            password="ClaveSegura123!",
        )

    def test_login_page_uses_custom_template(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_authenticated_user_without_photo_sees_uppercase_initials(self):
        self.user.first_name = "Ana"
        self.user.last_name = "Pérez"
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertRegex(response.content.decode(), r">\s*A\s*P\s*</span>")

    def test_valid_credentials_log_in_and_redirect_home(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.username, "password": "ClaveSegura123!"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_invalid_credentials_show_flash_message(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.username, "password": "incorrecta"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuario o contraseña incorrectos.")

    def test_logout_redirects_home_and_shows_flash_message(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"), follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Cerraste sesión correctamente.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_dashboard_authenticated_user_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/dashboard.html")
        self.assertContains(response, "Mi Perfil y Autogestión")
        self.assertContains(response, self.user.username)

    def test_dashboard_superuser_sees_admin_sections(self):
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Padrón de Matriculados")
        self.assertContains(response, "Cuentas de Usuarios")
        self.assertContains(response, "Roles y permisos")

    def test_dashboard_user_with_permission_sees_assigned_section(self):
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename="view_user", content_type__app_label="accounts")
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cuentas de Usuarios")


class PasswordRecoveryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="matriculado",
            email="matriculado@example.com",
            password="Temporal123!",
            must_change_password=True,
        )

    def test_password_reset_page_and_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email},
        )

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("password-reset", mail.outbox[0].body)

    def test_must_change_password_redirects_other_pages(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("accounts:password_change"))

    def test_password_change_clears_mandatory_flag(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "Temporal123!",
                "new_password1": "NuevaClaveSegura123!",
                "new_password2": "NuevaClaveSegura123!",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)

    def test_password_reset_clears_mandatory_flag(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        confirm_url = reverse("accounts:password_reset_confirm", args=[uid, token])
        self.client.get(confirm_url)
        response = self.client.post(
            reverse("accounts:password_reset_confirm", args=[uid, "set-password"]),
            {
                "new_password1": "NuevaClaveSegura456!",
                "new_password2": "NuevaClaveSegura456!",
            },
        )

        self.assertRedirects(response, reverse("accounts:password_reset_complete"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
