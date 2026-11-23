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
        HistorialEstadoMatricula.objects.create(
            matriculado=self.mat2,
            estado=HistorialEstadoMatricula.Estado.ACTIVA,
            fecha_desde=date(2022, 1, 1),
        )

        # Usuario 3: Inactivo (SUSPENDIDA o BAJA) - no debe figurar en directorio público
        self.user3 = User.objects.create_user(
            username="geologo3",
            first_name="Roberto",
            last_name="Inactivo",
            email="roberto@ejemplo.com",
        )
        self.mat3 = Matriculado.objects.create(
            usuario=self.user3,
            numero_matricula="MP-003",
            libro="1",
            folio="3",
            fecha_matriculacion=date(2023, 1, 1),
        )
        HistorialEstadoMatricula.objects.create(
            matriculado=self.mat3,
            estado=HistorialEstadoMatricula.Estado.SUSPENDIDA,
            fecha_desde=date(2023, 1, 1),
        )

    def test_directorio_publico_listado_y_busqueda(self):
        url = reverse("directory:public_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carlos García")
        self.assertContains(response, "Lucía Fernández")
        # Regla de fe pública (RF-07): Roberto (Suspendido) debe figurar en el directorio con su estado real
        self.assertContains(response, "Roberto Inactivo")
        self.assertContains(response, "MP-003")
        self.assertContains(response, "Matrícula Suspendida")

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
        self.universidad = Universidad.objects.create(nombre="Universidad de Buenos Aires", sigla="UBA", pais="AR")
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


class AntecedenteDisciplinarioTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_tribunal",
            password="AdminPassword123!",
            email="tribunal@geologos.com",
            must_change_password=False,
        )
        self.user = User.objects.create_user(
            username="geologo_sancionado",
            first_name="Pedro",
            last_name="Sancionado",
            dni="11223344",
            password="Password123!",
        )
        self.matriculado = Matriculado.objects.create(
            usuario=self.user,
            numero_matricula="MP-888",
            libro="1",
            folio="88",
            fecha_matriculacion=date(2022, 5, 10),
        )

    def test_creacion_antecedente_con_fecha_firmeza_obligatoria(self):
        hoy = timezone.now().date()
        antecedente = AntecedenteDisciplinario.objects.create(
            matriculado=self.matriculado,
            numero_expediente="EXP-2026-001",
            tipo_sancion=AntecedenteDisciplinario.TipoSancion.MULTA,
            monto_multa=50000.00,
            fecha_firmeza=hoy,
            descripcion="Incumplimiento del código de ética",
            creado_por=self.admin,
        )
        self.assertEqual(antecedente.matriculado, self.matriculado)
        self.assertEqual(antecedente.fecha_firmeza, hoy)
        self.assertEqual(antecedente.tipo_sancion, "MULTA")
        self.assertEqual(self.matriculado.antecedentes.count(), 1)

    def test_creacion_antecedente_desde_vista_dashboard(self):
        self.client.force_login(self.admin)
        url = reverse("directory:antecedente_create", kwargs={"matriculado_id": self.matriculado.pk})
        hoy = timezone.now().date()
        post_data = {
            "numero_expediente": "EXP-2026-002",
            "tipo_sancion": "SUSPENSION",
            "fecha_firmeza": hoy.strftime("%Y-%m-%d"),
            "fecha_inicio_suspension": hoy.strftime("%Y-%m-%d"),
            "fecha_fin_suspension": (hoy + timedelta(days=90)).strftime("%Y-%m-%d"),
            "descripcion": "Suspensión de matrícula por 90 días",
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": self.matriculado.pk}))

        ant = AntecedenteDisciplinario.objects.get(numero_expediente="EXP-2026-002")
        self.assertEqual(ant.matriculado, self.matriculado)
        self.assertEqual(ant.fecha_firmeza, hoy)
        self.assertEqual(ant.creado_por, self.admin)

    def test_formulario_falla_sin_fecha_firmeza(self):
        from apps.directory.forms import AntecedenteDisciplinarioForm
        form = AntecedenteDisciplinarioForm(data={
            "numero_expediente": "EXP-2026-003",
            "tipo_sancion": "APERCIBIMIENTO",
            "fecha_firmeza": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_firmeza", form.errors)


class HistorialEstadoTransitionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_estados",
            password="AdminPassword123!",
            must_change_password=False,
        )
        self.user = User.objects.create_user(
            username="geologo_estados",
            password="GeoPassword123!",
            must_change_password=False,
        )
        self.matriculado = Matriculado.objects.create(
            usuario=self.user,
            numero_matricula="MP-777",
            libro="1",
            folio="77",
            fecha_matriculacion=date(2020, 1, 1),
        )
        # Estado inicial: ACTIVA
        HistorialEstadoMatricula.objects.create(
            matriculado=self.matriculado,
            estado=HistorialEstadoMatricula.Estado.ACTIVA,
            fecha_desde=date(2020, 1, 1),
            motivo="Alta original",
        )
        self.antecedente = AntecedenteDisciplinario.objects.create(
            matriculado=self.matriculado,
            numero_expediente="EXP-ETH-2026",
            tipo_sancion=AntecedenteDisciplinario.TipoSancion.SUSPENSION,
            fecha_firmeza=timezone.now().date(),
        )

    def test_transicion_a_suspendida_vinculada_a_antecedente_bloquea_login(self):
        self.client.force_login(self.admin)
        hoy = timezone.now().date()
        url = reverse("directory:estado_create", kwargs={"matriculado_id": self.matriculado.pk})
        post_data = {
            "estado": HistorialEstadoMatricula.Estado.SUSPENDIDA,
            "fecha_desde": hoy.strftime("%Y-%m-%d"),
            "fecha_hasta": (hoy + timedelta(days=45)).strftime("%Y-%m-%d"),
            "motivo": "Resolución Tribunal de Disciplina",
            "origen_sancion": self.antecedente.pk,
            "resolucion_acta": "Acta 102/2026",
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": self.matriculado.pk}))

        self.assertEqual(self.matriculado.estado_actual.estado, HistorialEstadoMatricula.Estado.SUSPENDIDA)
        self.assertEqual(self.matriculado.estado_actual.origen_sancion, self.antecedente)

        # Verificar bloqueo de inicio de sesión
        self.client.logout()
        res_login = self.client.post(
            reverse("accounts:login"),
            {"username": "geologo_estados", "password": "GeoPassword123!"},
        )
        self.assertEqual(res_login.status_code, 200)
        self.assertContains(res_login, "suspendida hasta el")

    def test_transicion_a_baja_bloquea_login(self):
        self.client.force_login(self.admin)
        hoy = timezone.now().date()
        url = reverse("directory:estado_create", kwargs={"matriculado_id": self.matriculado.pk})
        post_data = {
            "estado": HistorialEstadoMatricula.Estado.BAJA,
            "fecha_desde": hoy.strftime("%Y-%m-%d"),
            "motivo": "Cancelación definitiva de matrícula",
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": self.matriculado.pk}))

        self.assertEqual(self.matriculado.estado_actual.estado, HistorialEstadoMatricula.Estado.BAJA)

        self.client.logout()
        res_login = self.client.post(
            reverse("accounts:login"),
            {"username": "geologo_estados", "password": "GeoPassword123!"},
        )
        self.assertEqual(res_login.status_code, 200)
        self.assertContains(res_login, "dada de baja")


class TituloManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_titulos",
            password="AdminPassword123!",
            must_change_password=False,
        )
        self.user = User.objects.create_user(
            username="geologo_titulos",
            password="GeoPassword123!",
            must_change_password=False,
        )
        self.matriculado = Matriculado.objects.create(
            usuario=self.user,
            numero_matricula="MP-555",
            libro="1",
            folio="55",
            fecha_matriculacion=date(2022, 1, 1),
        )
        self.universidad = Universidad.objects.create(nombre="Universidad Nacional de Tucumán", sigla="UNT", pais="AR")

    def test_crear_titulo_para_matriculado(self):
        self.client.force_login(self.admin)
        url = reverse("directory:titulo_create", kwargs={"matriculado_id": self.matriculado.pk})
        post_data = {
            "denominacion": "Doctor en Ciencias Geológicas",
            "tipo": Titulo.TipoTitulo.POSGRADO,
            "emitido_por": self.universidad.pk,
            "fecha_egreso": "2024-03-15",
            "fecha_expedicion": "2024-09-20",
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": self.matriculado.pk}))
        self.assertEqual(self.matriculado.titulos.count(), 1)
        tit = self.matriculado.titulos.first()
        self.assertEqual(tit.denominacion, "Doctor en Ciencias Geológicas")
        self.assertEqual(tit.emitido_por, self.universidad)

    def test_editar_titulo_existente(self):
        self.client.force_login(self.admin)
        titulo = Titulo.objects.create(
            matriculado=self.matriculado,
            denominacion="Licenciatura en Geología",
            tipo=Titulo.TipoTitulo.GRADO,
            emitido_por=self.universidad,
        )
        url = reverse("directory:titulo_edit", kwargs={"pk": titulo.pk})
        post_data = {
            "denominacion": "Licenciado en Geología (Corregido)",
            "tipo": Titulo.TipoTitulo.GRADO,
            "emitido_por": self.universidad.pk,
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": self.matriculado.pk}))
        titulo.refresh_from_db()
        self.assertEqual(titulo.denominacion, "Licenciado en Geología (Corregido)")


class AjaxCreationEndpointsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_ajax",
            password="AdminPassword123!",
            must_change_password=False,
        )

    def test_crear_especialidad_ajax_exitoso(self):
        self.client.force_login(self.admin)
        url = reverse("directory:especialidad_create_ajax")
        response = self.client.post(url, {"nombre": "Geofísica Aplicada"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("nombre"), "Geofísica Aplicada")
        self.assertTrue(Especialidad.objects.filter(nombre="Geofísica Aplicada").exists())

    def test_crear_especialidad_ajax_duplicada_retorna_400(self):
        self.client.force_login(self.admin)
        Especialidad.objects.create(nombre="Vulcanología")
        url = reverse("directory:especialidad_create_ajax")
        response = self.client.post(url, {"nombre": "Vulcanología"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))

    def test_crear_universidad_ajax_exitoso(self):
        self.client.force_login(self.admin)
        url = reverse("directory:universidad_create_ajax")
        response = self.client.post(url, {
            "nombre": "Universidad Nacional de Cuyo",
            "sigla": "UNCuyo",
            "pais": "AR",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("UNCuyo", data.get("nombre"))
        self.assertTrue(Universidad.objects.filter(sigla="UNCuyo").exists())


class MatriculadoUpdateViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_update",
            password="AdminPassword123!",
            must_change_password=False,
        )
        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="UserPassword123!",
            must_change_password=False,
        )
        self.matriculado = Matriculado.objects.create(
            usuario=self.regular_user,
            numero_matricula="MP-321",
            libro="1",
            folio="32",
            fecha_matriculacion=date(2021, 6, 15),
            domicilio_profesional_calle="Calle Falsa",
            domicilio_profesional_numero="123",
            domicilio_profesional_localidad="Capital",
            domicilio_profesional_provincia="Catamarca",
            domicilio_profesional_pais="AR",
        )

    def test_admin_puede_editar_matriculado(self):
        self.client.force_login(self.admin)
        url = reverse("directory:matriculado_edit", kwargs={"pk": self.matriculado.pk})
        post_data = {
            "usuario": self.regular_user.pk,
            "numero_matricula": "MP-321",
            "libro": "1",
            "folio": "32",
            "fecha_matriculacion": "2021-06-15",
            "domicilio_profesional_calle": "Av. Presidente Castillo",
            "domicilio_profesional_numero": "500",
            "domicilio_profesional_localidad": "San Fernando",
            "domicilio_profesional_provincia": "Catamarca",
            "domicilio_profesional_pais": "AR",
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse("directory:matriculado_detail", kwargs={"pk": self.matriculado.pk}))
        self.matriculado.refresh_from_db()
        self.assertEqual(self.matriculado.domicilio_profesional_calle, "Av. Presidente Castillo")

    def test_usuario_sin_permisos_no_puede_editar_matriculado(self):
        self.client.force_login(self.regular_user)
        url = reverse("directory:matriculado_edit", kwargs={"pk": self.matriculado.pk})
        response = self.client.get(url)
        # PermissionRequiredMixin returns 403 Forbidden
        self.assertEqual(response.status_code, 403)



