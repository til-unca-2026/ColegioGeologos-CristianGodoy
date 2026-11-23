from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Contenido
from apps.directory.models import Especialidad, Matriculado
from apps.documents.models import Documento

User = get_user_model()


class HomeViewTests(TestCase):
    def setUp(self):
        self.hoy = timezone.now()
        self.admin = User.objects.create_superuser(
            username="admin_home",
            password="AdminPass123!",
            email="admin@home.com",
            must_change_password=False,
        )
        self.matriculado_user = User.objects.create_user(
            username="geologo_home",
            password="GeoPass123!",
            email="geologo@home.com",
            must_change_password=False,
        )
        self.matriculado = Matriculado.objects.create(
            usuario=self.matriculado_user,
            numero_matricula="MP-101",
            libro="1",
            folio="101",
            fecha_matriculacion=date(2021, 1, 1),
        )
        self.especialidad = Especialidad.objects.create(nombre="Hidrogeología")

        # Novedad pública
        self.nov_publica = Contenido.objects.create(
            titulo="Noticia Geológica Abierta",
            tipo=Contenido.Tipo.NOTICIA,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            visibilidad=Contenido.Visibilidad.PUBLICO,
            fecha_publicacion=self.hoy - timedelta(days=1),
            creado_por=self.admin,
        )
        # Novedad solo para matriculados
        self.nov_matriculados = Contenido.objects.create(
            titulo="Noticia Exclusiva Matriculados",
            tipo=Contenido.Tipo.NOTICIA,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            visibilidad=Contenido.Visibilidad.MATRICULADOS,
            fecha_publicacion=self.hoy - timedelta(days=1),
            creado_por=self.admin,
        )
        # Documento público
        self.doc_publico = Documento.objects.create(
            titulo="Reglamento Público",
            categoria=Documento.Categoria.RESOLUCION,
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )
        # Documento interno
        self.doc_interno = Documento.objects.create(
            titulo="Balance Interno",
            categoria=Documento.Categoria.RESOLUCION,
            visibilidad=Documento.Visibilidad.INTERNO,
            vigente=True,
            creado_por=self.admin,
        )

    def test_home_anonimo_acceso_y_visibilidad(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

        # Noticias en contexto
        noticias = list(response.context["home_noticias"])
        self.assertIn(self.nov_publica, noticias)
        self.assertNotIn(self.nov_matriculados, noticias)

        # Documentos en contexto
        docs = list(response.context["home_documentos"])
        self.assertIn(self.doc_publico, docs)
        self.assertNotIn(self.doc_interno, docs)

        # Métrica de matriculados
        self.assertEqual(response.context["total_matriculados"], 1)

    def test_home_matriculado_ve_contenido_exclusivo(self):
        self.client.force_login(self.matriculado_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        noticias = list(response.context["home_noticias"])
        self.assertIn(self.nov_publica, noticias)
        self.assertIn(self.nov_matriculados, noticias)

    def test_home_staff_ve_todos_los_documentos(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        docs = list(response.context["home_documentos"])
        self.assertIn(self.doc_publico, docs)
        self.assertIn(self.doc_interno, docs)


class BeneficiosViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_ben",
            password="AdminPass123!",
            must_change_password=False,
        )
        self.ben1 = Contenido.objects.create(
            titulo="Descuento en Hotel Catamarca",
            resumen="20% de descuento en alojamiento",
            cuerpo="Convenio vigente con el gremio hotelero",
            tipo=Contenido.Tipo.BENEFICIO,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            visibilidad=Contenido.Visibilidad.PUBLICO,
            fecha_publicacion=timezone.now() - timedelta(days=2),
            creado_por=self.admin,
        )
        self.ben2 = Contenido.objects.create(
            titulo="Seguro de Mala Praxis Profesional",
            resumen="Póliza colectiva para geólogos",
            cuerpo="Cobertura amplia en proyectos mineros",
            tipo=Contenido.Tipo.BENEFICIO,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            visibilidad=Contenido.Visibilidad.PUBLICO,
            fecha_publicacion=timezone.now() - timedelta(days=1),
            creado_por=self.admin,
        )

    def test_beneficios_list_status_and_template(self):
        response = self.client.get(reverse("beneficios"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "beneficios.html")
        self.assertEqual(response.context["total_beneficios"], 2)

    def test_beneficios_busqueda_filtra_correctamente(self):
        response = self.client.get(reverse("beneficios"), {"q": "Hotel"})
        self.assertEqual(response.status_code, 200)
        beneficios = list(response.context["beneficios"])
        self.assertIn(self.ben1, beneficios)
        self.assertNotIn(self.ben2, beneficios)
        self.assertEqual(response.context["q"], "Hotel")

    def test_convenios_retrocompatible_alias(self):
        response = self.client.get(reverse("convenios"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.ben1, response.context["beneficios"])


class ConvocatoriasLaboralesViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_conv",
            password="AdminPass123!",
            must_change_password=False,
        )
        self.conv1 = Contenido.objects.create(
            titulo="Búsqueda de Geólogo de Exploración",
            resumen="Empresa minera busca profesional senior",
            tipo=Contenido.Tipo.CONVOCATORIA,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            visibilidad=Contenido.Visibilidad.PUBLICO,
            fecha_publicacion=timezone.now() - timedelta(days=2),
            creado_por=self.admin,
        )
        self.conv2 = Contenido.objects.create(
            titulo="Consultor Ambiental para Proyecto Vial",
            resumen="Estudios de impacto ambiental en cordillera",
            tipo=Contenido.Tipo.CONVOCATORIA,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            visibilidad=Contenido.Visibilidad.PUBLICO,
            fecha_publicacion=timezone.now() - timedelta(days=1),
            creado_por=self.admin,
        )

    def test_convocatorias_list_status_and_template(self):
        response = self.client.get(reverse("convocatorias"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "convocatorias.html")
        self.assertEqual(response.context["total_convocatorias"], 2)

    def test_convocatorias_busqueda_filtra_correctamente(self):
        response = self.client.get(reverse("convocatorias"), {"q": "Exploración"})
        self.assertEqual(response.status_code, 200)
        convocatorias = list(response.context["convocatorias"])
        self.assertIn(self.conv1, convocatorias)
        self.assertNotIn(self.conv2, convocatorias)


class ServiciosProfesionalesViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_serv",
            password="AdminPass123!",
            must_change_password=False,
        )
        self.doc_arancel = Documento.objects.create(
            titulo="Tabla de Aranceles Sugeridos 2026",
            categoria=Documento.Categoria.ARANCEL,
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )
        self.doc_otro = Documento.objects.create(
            titulo="Resolución de Directorio N° 12",
            categoria=Documento.Categoria.RESOLUCION,
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )

    def test_servicios_profesionales_muestra_solo_aranceles(self):
        response = self.client.get(reverse("servicios_profesionales"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "servicios_profesionales.html")

        aranceles = list(response.context["documentos_aranceles"])
        self.assertIn(self.doc_arancel, aranceles)
        self.assertNotIn(self.doc_otro, aranceles)


class StaticPagesTests(TestCase):
    def test_quienes_somos_page(self):
        response = self.client.get(reverse("quienes_somos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "quienes_somos.html")

    def test_site_under_construction_page(self):
        response = self.client.get(reverse("site_under_construction"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "site_under_construction.html")
