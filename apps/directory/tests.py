from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.directory.models import (
    AntecedenteDisciplinario,
    Especialidad,
    HistorialEstadoMatricula,
    Matriculado,
    Titulo,
    Universidad,
)

User = get_user_model()


class DirectoryModelAndLoginRestrictionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="geologo_test",
            password="Password123!",
            first_name="Juan",
            last_name="Pérez",
            dni="12345678",
            must_change_password=False,
        )
        self.matriculado = Matriculado.objects.create(
            usuario=self.user,
            numero_matricula="MP-100",
            libro="1",
            folio="10",
            fecha_matriculacion=date(2020, 1, 1),
        )
        self.universidad = Universidad.objects.create(nombre="Universidad Nacional de Catamarca", sigla="UNCA")
        self.especialidad = Especialidad.objects.create(nombre="Hidrogeología")
        self.matriculado.especialidades.add(self.especialidad)

    def test_matriculado_estado_actual_inicial_sin_estados(self):
        self.assertIsNone(self.matriculado.estado_actual)
        puede, msg = self.matriculado.puede_iniciar_sesion()
        self.assertTrue(puede)

    def test_matriculado_activa_puede_iniciar_sesion(self):
        HistorialEstadoMatricula.objects.create(
            matriculado=self.matriculado,
            estado=HistorialEstadoMatricula.Estado.ACTIVA,
            fecha_desde=date(2020, 1, 1),
            motivo="Alta original",
        )
        self.assertEqual(self.matriculado.estado_actual.estado, HistorialEstadoMatricula.Estado.ACTIVA)
        puede, msg = self.matriculado.puede_iniciar_sesion()
        self.assertTrue(puede)
        self.assertEqual(msg, "")

        # Test login HTTP exitoso
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "geologo_test", "password": "Password123!"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_matriculado_baja_no_puede_iniciar_sesion(self):
        HistorialEstadoMatricula.objects.create(
            matriculado=self.matriculado,
            estado=HistorialEstadoMatricula.Estado.BAJA,
            fecha_desde=timezone.now().date(),
            motivo="Solicitud de baja voluntaria",
        )
        self.assertEqual(self.matriculado.estado_actual.estado, HistorialEstadoMatricula.Estado.BAJA)
        puede, msg = self.matriculado.puede_iniciar_sesion()
        self.assertFalse(puede)
        self.assertIn("baja", msg.lower())

        # Test login HTTP bloqueado
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "geologo_test", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dada de baja")

    def test_matriculado_suspension_vigente_no_puede_iniciar_sesion(self):
        hoy = timezone.now().date()
        HistorialEstadoMatricula.objects.create(
            matriculado=self.matriculado,
            estado=HistorialEstadoMatricula.Estado.SUSPENDIDA,
            fecha_desde=hoy - timedelta(days=5),
            fecha_hasta=hoy + timedelta(days=30),
            motivo="Sanción del tribunal de ética",
        )
        puede, msg = self.matriculado.puede_iniciar_sesion()
        self.assertFalse(puede)
        self.assertIn("suspendida hasta", msg.lower())

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "geologo_test", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "suspendida hasta el")

    def test_matriculado_suspension_vencida_recupera_acceso(self):
        hoy = timezone.now().date()
        # Suspensión que terminó ayer
        HistorialEstadoMatricula.objects.create(
            matriculado=self.matriculado,
            estado=HistorialEstadoMatricula.Estado.SUSPENDIDA,
            fecha_desde=hoy - timedelta(days=60),
            fecha_hasta=hoy - timedelta(days=1),
            motivo="Sanción cumplida",
        )
        puede, msg = self.matriculado.puede_iniciar_sesion()
        self.assertTrue(puede)

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "geologo_test", "password": "Password123!"},
        )
        self.assertRedirects(response, reverse("home"))


class DirectoryPublicViewsTests(TestCase):
    def setUp(self):
        # Usuario 1: publica teléfono pero no email
        self.user1 = User.objects.create_user(
            username="geologo1",
            first_name="Carlos",
            last_name="García",
            email="carlos@ejemplo.com",
            phone="+543834111111",
            publicar_email=False,
            publicar_telefono=True,
        )
        self.mat1 = Matriculado.objects.create(
            usuario=self.user1,
            numero_matricula="MP-001",
            libro="1",
            folio="1",
            fecha_matriculacion=date(2021, 1, 1),
            domicilio_profesional_calle="San Martín",
            domicilio_profesional_numero="450",
            domicilio_profesional_localidad="San Fernando del Valle",
        )
        self.esp_mineria = Especialidad.objects.create(nombre="Minería")
        self.mat1.especialidades.add(self.esp_mineria)
        HistorialEstadoMatricula.objects.create(
            matriculado=self.mat1,
            estado=HistorialEstadoMatricula.Estado.ACTIVA,
            fecha_desde=date(2021, 1, 1),
        )

        # Usuario 2: no publica teléfono ni email
        self.user2 = User.objects.create_user(
            username="geologo2",
            first_name="Lucía",
            last_name="Fernández",
            email="lucia@ejemplo.com",
            phone="+543834222222",
            publicar_email=False,
            publicar_telefono=False,
        )
        self.mat2 = Matriculado.objects.create(
            usuario=self.user2,
            numero_matricula="MP-002",
            libro="1",
            folio="2",
            fecha_matriculacion=date(2022, 1, 1),
        )
        self.esp_geo = Especialidad.objects.create(nombre="Geotecnia")
        self.mat2.especialidades.add(self.esp_geo)

    def test_directorio_publico_listado_y_busqueda(self):
        url = reverse("directory:public_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carlos García")
        self.assertContains(response, "Lucía Fernández")

        # Búsqueda por texto (nombre)
        res_busqueda = self.client.get(url, {"q": "Carlos"})
        self.assertEqual(res_busqueda.status_code, 200)
        self.assertContains(res_busqueda, "Carlos García")
        self.assertNotContains(res_busqueda, "Lucía Fernández")

        # Filtro por especialidad
        res_esp = self.client.get(url, {"especialidad": self.esp_geo.id})
        self.assertEqual(res_esp.status_code, 200)
        self.assertContains(res_esp, "Lucía Fernández")
        self.assertNotContains(res_esp, "Carlos García")

    def test_directorio_publico_privacidad_ley_25326(self):
        # Detalle de Carlos: debe mostrar teléfono pero NO email
        url_carlos = reverse("directory:public_detail", kwargs={"pk": self.mat1.pk})
        res_carlos = self.client.get(url_carlos)
        self.assertEqual(res_carlos.status_code, 200)
        self.assertContains(res_carlos, "+543834111111")
        self.assertNotContains(res_carlos, "carlos@ejemplo.com")

        # Detalle de Lucía: no debe mostrar ni email ni teléfono
        url_lucia = reverse("directory:public_detail", kwargs={"pk": self.mat2.pk})
        res_lucia = self.client.get(url_lucia)
        self.assertEqual(res_lucia.status_code, 200)
        self.assertNotContains(res_lucia, "lucia@ejemplo.com")
        self.assertNotContains(res_lucia, "+543834222222")


class MatriculadoCreateViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_test",
            password="AdminPassword123!",
            email="admin@geologos.com",
            must_change_password=False,
        )
        self.target_user = User.objects.create_user(
            username="candidato_matricula",
            first_name="Roberto",
            last_name="Gómez",
            dni="99888777",
            password="Password123!",
        )
        self.universidad = Universidad.objects.create(nombre="Universidad de Buenos Aires", sigla="UBA")
        self.especialidad = Especialidad.objects.create(nombre="Medio Ambiente")

    def test_creacion_atomica_matriculado_con_titulo_y_estado(self):
        self.client.force_login(self.admin)
        url = reverse("directory:matriculado_create")
        post_data = {
            "usuario": self.target_user.pk,
            "numero_matricula": "MP-999",
            "libro": "2",
            "folio": "50",
            "fecha_matriculacion": "2026-11-10",
            "especialidades": [self.especialidad.pk],
            "domicilio_profesional_calle": "Rivadavia",
            "domicilio_profesional_numero": "100",
            "domicilio_profesional_localidad": "Capital",
            "domicilio_profesional_provincia": "Catamarca",
            "domicilio_profesional_pais": "AR",
            # Datos del título con prefix="titulo"
            "titulo-denominacion": "Licenciado en Ciencias Geológicas",
            "titulo-tipo": Titulo.TipoTitulo.GRADO,
            "titulo-emitido_por": self.universidad.pk,
            "titulo-fecha_egreso": "2025-12-15",
            "titulo-fecha_expedicion": "2026-03-20",
        }
        response = self.client.post(url, post_data)
        mat = Matriculado.objects.filter(numero_matricula="MP-999").first()
        self.assertIsNotNone(mat)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": mat.pk}))

        # Verificamos que se crearon Matriculado, Titulo e HistorialEstado
        self.assertEqual(mat.usuario, self.target_user)
        self.assertEqual(mat.titulos.count(), 1)
        self.assertEqual(mat.titulos.first().denominacion, "Licenciado en Ciencias Geológicas")
        self.assertEqual(mat.estados.count(), 1)
        self.assertEqual(mat.estado_actual.estado, HistorialEstadoMatricula.Estado.ACTIVA)

