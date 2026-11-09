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
            must_change_password=False,
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


class DashboardViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="geologo",
            password="ClaveSegura123!",
            must_change_password=False,
        )

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


class UserManagementViewsTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group, Permission
        user_model = get_user_model()

        self.group_admin, _ = Group.objects.get_or_create(name="Administradores")
        self.group_colab, _ = Group.objects.get_or_create(name="Colaboradores")
        self.group_matr, _ = Group.objects.get_or_create(name="Matriculados")

        self.admin_user = user_model.objects.create_superuser(
            username="admin_super",
            email="admin@example.com",
            password="AdminPassword123!",
            must_change_password=False,
        )

        self.regular_user = user_model.objects.create_user(
            username="usuario_comun",
            email="comun@example.com",
            password="UserPassword123!",
            must_change_password=False,
        )

    def test_user_create_requires_add_user_permission(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("accounts:user_create"))
        self.assertEqual(response.status_code, 403)

    def test_user_create_view_accessible_by_admin(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("accounts:user_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/user_form.html")
        self.assertContains(response, "Crear nuevo usuario")
        self.assertContains(response, "Administradores")
        self.assertContains(response, "Colaboradores")
        self.assertContains(response, "Matriculados")

    def test_user_create_post_success_assigns_group_and_redirects(self):
        self.client.force_login(self.admin_user)
        data = {
            "username": "nuevo_colaborador",
            "email": "colaborador@example.com",
            "first_name": "Juan",
            "last_name": "Perez",
            "password": "PasswordTemporal123!",
            "group": self.group_colab.pk,
            "dni": "35123456",
            "cuil_cuit": "20-35123456-8",
            "fecha_nacimiento": "1990-05-15",
            "lugar_nacimiento": "San Fernando del Valle de Catamarca",
            "nacionalidad": "AR",
            "phone": "+543834111222",
            "domicilio_real_calle": "San Martin",
            "domicilio_real_numero": "550",
            "domicilio_real_piso_depto": "1 B",
            "domicilio_real_localidad": "San Fernando del Valle",
            "domicilio_real_provincia": "Catamarca",
            "domicilio_real_pais": "AR",
            "domicilio_real_cp": "4700",
            "publicar_email": "on",
            "publicar_telefono": "on",
            "must_change_password": "on",
            "is_active": "on",
        }
        response = self.client.post(reverse("accounts:user_create"), data)
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=admin_usuarios")

        User = get_user_model()
        new_user = User.objects.get(username="nuevo_colaborador")
        self.assertEqual(new_user.email, "colaborador@example.com")
        self.assertEqual(new_user.dni, "35123456")
        self.assertEqual(new_user.cuil_cuit, "20-35123456-8")
        self.assertEqual(str(new_user.fecha_nacimiento), "1990-05-15")
        self.assertEqual(new_user.domicilio_real_calle, "San Martin")
        self.assertTrue(new_user.publicar_email)
        self.assertTrue(new_user.publicar_telefono)
        self.assertTrue(new_user.must_change_password)
        self.assertTrue(new_user.is_active)
        self.assertFalse(new_user.is_staff)  # REGLA: Nunca es staff
        self.assertEqual(new_user.creado_por, self.admin_user)
        self.assertIn(self.group_colab, new_user.groups.all())
        self.assertTrue(new_user.check_password("PasswordTemporal123!"))

    def test_user_edit_requires_change_user_permission(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("accounts:user_edit", args=[self.regular_user.pk]))
        self.assertEqual(response.status_code, 403)

    def test_user_edit_view_accessible_by_admin(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("accounts:user_edit", args=[self.regular_user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/user_form.html")
        self.assertContains(response, f"Editar usuario: {self.regular_user.username}")

    def test_user_edit_post_success_updates_group_and_data(self):
        self.client.force_login(self.admin_user)
        data = {
            "username": self.regular_user.username,
            "email": "comun_modificado@example.com",
            "first_name": "NombreModificado",
            "last_name": "ApellidoModificado",
            "group": self.group_matr.pk,
            "dni": "40987654",
            "cuil_cuit": "20-40987654-7",
            "fecha_nacimiento": "1995-10-20",
            "lugar_nacimiento": "Andalgalá, Catamarca",
            "nacionalidad": "AR",
            "phone": "+543834999888",
            "domicilio_real_calle": "Rivadavia",
            "domicilio_real_numero": "120",
            "domicilio_real_localidad": "Andalgalá",
            "domicilio_real_provincia": "Catamarca",
            "domicilio_real_pais": "AR",
            "domicilio_real_cp": "4740",
            "is_active": "on",
        }
        response = self.client.post(reverse("accounts:user_edit", args=[self.regular_user.pk]), data)
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=admin_usuarios")

        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.email, "comun_modificado@example.com")
        self.assertEqual(self.regular_user.first_name, "NombreModificado")
        self.assertEqual(self.regular_user.dni, "40987654")
        self.assertFalse(self.regular_user.is_staff)  # REGLA: Nunca es staff
        self.assertEqual(self.regular_user.modificado_por, self.admin_user)
        self.assertIn(self.group_matr, self.regular_user.groups.all())


class MembresiaComisionModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="vocal1",
            password="Password123!",
            first_name="Carlos",
            last_name="Gomez",
        )

    def test_crear_membresia_y_vigencia(self):
        from datetime import date, timedelta
        from apps.accounts.models import MembresiaComision

        hoy = date.today()
        membresia = MembresiaComision.objects.create(
            usuario=self.user,
            comision=MembresiaComision.Comision.DIRECTIVA,
            cargo=MembresiaComision.Cargo.PRESIDENTE,
            fecha_desde=hoy - timedelta(days=30),
            fecha_hasta=hoy + timedelta(days=365),
        )
        self.assertTrue(membresia.es_vigente)
        self.assertIn("Presidente", str(membresia))
        self.assertEqual(self.user.cargos.count(), 1)


class MembresiaComisionDashboardViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username="admin_comision",
            password="AdminPassword123!",
            must_change_password=False,
        )
        self.geologo = user_model.objects.create_user(
            username="geologo_miembro",
            password="UserPassword123!",
            first_name="Laura",
            last_name="Fernandez",
            must_change_password=False,
        )

    def test_dashboard_muestra_tab_comision_para_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(f"{reverse('accounts:dashboard')}?tab=admin_comision")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cargos y Comisiones")
        self.assertContains(response, "Asignar Cargo")

    def test_crear_membresia_desde_dashboard(self):
        from datetime import date
        from apps.accounts.models import MembresiaComision
        self.client.force_login(self.admin)

        data = {
            "usuario": self.geologo.pk,
            "comision": "DIRECTIVA",
            "cargo": "TESORERO",
            "fecha_desde": "2026-01-01",
            "fecha_hasta": "",
        }
        response = self.client.post(reverse("accounts:comision_create"), data)
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=admin_comision")

        membresia = MembresiaComision.objects.get(usuario=self.geologo)
        self.assertEqual(membresia.cargo, "TESORERO")
        self.assertEqual(membresia.creado_por, self.admin)
        self.assertTrue(membresia.es_vigente)

    def test_finalizar_mandato_comision_desde_dashboard(self):
        from datetime import date
        from apps.accounts.models import MembresiaComision
        membresia = MembresiaComision.objects.create(
            usuario=self.geologo,
            comision="DIRECTIVA",
            cargo="SECRETARIO",
            fecha_desde=date(2025, 1, 1),
            fecha_hasta=None,
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("accounts:comision_finalizar", args=[membresia.pk]))
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=admin_comision")

        membresia.refresh_from_db()
        self.assertIsNotNone(membresia.fecha_hasta)
        self.assertEqual(membresia.modificado_por, self.admin)

    def test_usuario_puede_actualizar_su_propio_perfil_desde_dashboard(self):
        self.client.force_login(self.geologo)
        data = {
            "email": "laura.nueva@example.com",
            "phone": "+543834112233",
            "publicar_email": "on",
            "publicar_telefono": "on",
            "domicilio_real_calle": "Av. Belgrano",
            "domicilio_real_numero": "450",
            "domicilio_real_piso_depto": "1 A",
            "domicilio_real_localidad": "San Fernando del Valle de Catamarca",
            "domicilio_real_provincia": "Catamarca",
            "domicilio_real_pais": "AR",
            "domicilio_real_cp": "4700",
        }
        response = self.client.post(reverse("accounts:dashboard"), data)
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=perfil")

        self.geologo.refresh_from_db()
        self.assertEqual(self.geologo.email, "laura.nueva@example.com")
        self.assertEqual(str(self.geologo.phone), "+543834112233")
        self.assertTrue(self.geologo.publicar_email)
        self.assertTrue(self.geologo.publicar_telefono)
        self.assertEqual(self.geologo.domicilio_real_calle, "Av. Belgrano")
        self.assertEqual(self.geologo.domicilio_real_localidad, "San Fernando del Valle de Catamarca")
        self.assertEqual(self.geologo.modificado_por, self.geologo)

