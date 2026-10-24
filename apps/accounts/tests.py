from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
