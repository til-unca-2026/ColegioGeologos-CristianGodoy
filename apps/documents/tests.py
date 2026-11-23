from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.documents.models import Documento

User = get_user_model()


class DocumentoDashboardAndAdminViewsTests(TestCase):
    def setUp(self):
        # Grupos
        self.grupo_admin, _ = Group.objects.get_or_create(name="Administradores")
        self.grupo_matriculados, _ = Group.objects.get_or_create(name="Matriculados")

        # Usuarios
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="Password123!",
            must_change_password=False,
            first_name="Admin",
            last_name="Geologo",
            dni="10000001",
            cuil_cuit="20100000019",
            fecha_nacimiento="1980-01-01",
            lugar_nacimiento="Catamarca",
            domicilio_real_calle="Calle San Martin",
            domicilio_real_numero="100",
            domicilio_real_localidad="Capital",
            domicilio_real_provincia="Catamarca",
            domicilio_real_cp="4700",
        )
        self.admin.groups.add(self.grupo_admin)

        self.matriculado = User.objects.create_user(
            username="matriculado_user",
            email="mat@test.com",
            password="Password123!",
            must_change_password=False,
            first_name="Juan",
            last_name="Perez",
            dni="20000002",
            cuil_cuit="20200000029",
            fecha_nacimiento="1990-05-10",
            lugar_nacimiento="Catamarca",
            domicilio_real_calle="Calle Rivadavia",
            domicilio_real_numero="200",
            domicilio_real_localidad="Capital",
            domicilio_real_provincia="Catamarca",
            domicilio_real_cp="4700",
        )
        self.matriculado.groups.add(self.grupo_matriculados)

    def test_anonymous_cannot_access_documento_create(self):
        url = reverse("documents:documento_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_matriculado_cannot_access_documento_create(self):
        self.client.force_login(self.matriculado)
        url = reverse("documents:documento_create")
        response = self.client.get(url)
        # Redirigido al dashboard con mensaje de error
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_admin_can_access_documento_create_page(self):
        self.client.force_login(self.admin)
        url = reverse("documents:documento_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cargar Nuevo Documento Institucional")

    @patch("core.storage.SupabaseStorage._save", return_value="documentos/res_12_2024.pdf")
    def test_admin_can_create_documento(self, mock_storage_save):
        self.client.force_login(self.admin)
        url = reverse("documents:documento_create")
        pdf_file = SimpleUploadedFile("res_12_2024.pdf", b"%PDF-1.4 test content", content_type="application/pdf")

        data = {
            "numero": "Res. 12/2024",
            "titulo": "Reglamento Electoral",
            "categoria": Documento.Categoria.REGLAMENTO,
            "fecha_documento": "2024-03-15",
            "descripcion": "Normas para la elección de autoridades.",
            "archivo_almacenado": pdf_file,
            "visibilidad": Documento.Visibilidad.PUBLICO,
            "vigente": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=admin_documentos")

        doc = Documento.objects.filter(numero="Res. 12/2024").first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.titulo, "Reglamento Electoral")
        self.assertEqual(doc.creado_por, self.admin)
        self.assertTrue(doc.vigente)

    @patch("core.storage.SupabaseStorage._save", return_value="documentos/doc.pdf")
    def test_dashboard_displays_documentos_tab_for_admin(self, mock_storage_save):
        self.client.force_login(self.admin)
        doc = Documento.objects.create(
            numero="Ley 4118",
            titulo="Ley de Creación del Colegio",
            categoria=Documento.Categoria.LEY,
            descripcion="Ley fundacional",
            archivo_almacenado=SimpleUploadedFile("doc.pdf", b"%PDF-1.4 ..."),
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )

        response = self.client.get(f"{reverse('accounts:dashboard')}?tab=admin_documentos")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ley 4118")
        self.assertContains(response, "Ley de Creación del Colegio")

    @patch("core.storage.SupabaseStorage._save", return_value="documentos/doc.pdf")
    def test_public_documentos_list_visibility_rules(self, mock_storage_save):
        # Crear documento público
        doc_pub = Documento.objects.create(
            numero="Res. 01/2024",
            titulo="Estatuto Público",
            categoria=Documento.Categoria.ESTATUTO,
            descripcion="Público para todos",
            archivo_almacenado=SimpleUploadedFile("doc1.pdf", b"%PDF-1.4 ..."),
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )
        # Crear documento exclusivo matriculados
        doc_mat = Documento.objects.create(
            numero="Res. 02/2024",
            titulo="Resolución Arancelaria",
            categoria=Documento.Categoria.RESOLUCION,
            descripcion="Solo para matriculados",
            archivo_almacenado=SimpleUploadedFile("doc2.pdf", b"%PDF-1.4 ..."),
            visibilidad=Documento.Visibilidad.MATRICULADOS,
            vigente=True,
            creado_por=self.admin,
        )
        # Crear documento interno
        doc_int = Documento.objects.create(
            numero="Acta 03/2024",
            titulo="Acta Reservada",
            categoria=Documento.Categoria.OTRO,
            descripcion="Solo comisión/admin",
            archivo_almacenado=SimpleUploadedFile("doc3.pdf", b"%PDF-1.4 ..."),
            visibilidad=Documento.Visibilidad.INTERNO,
            vigente=True,
            creado_por=self.admin,
        )

        url = reverse("documents:documento_list")

        # 1. Visitante anónimo: solo ve el público
        res_anon = self.client.get(url)
        self.assertEqual(res_anon.status_code, 200)
        self.assertContains(res_anon, "Estatuto Público")
        self.assertNotContains(res_anon, "Resolución Arancelaria")
        self.assertNotContains(res_anon, "Acta Reservada")

        # 2. Matriculado logueado: ve público y matriculados, pero NO interno
        self.client.force_login(self.matriculado)
        res_mat = self.client.get(url)
        self.assertEqual(res_mat.status_code, 200)
        self.assertContains(res_mat, "Estatuto Público")
        self.assertContains(res_mat, "Resolución Arancelaria")
        self.assertNotContains(res_mat, "Acta Reservada")

        # 3. Administrador: ve todos
        self.client.force_login(self.admin)
        res_admin = self.client.get(url)
        self.assertEqual(res_admin.status_code, 200)
        self.assertContains(res_admin, "Estatuto Público")
        self.assertContains(res_admin, "Resolución Arancelaria")
        self.assertContains(res_admin, "Acta Reservada")

    @patch("core.storage.SupabaseStorage._save", return_value="documentos/doc_update.pdf")
    def test_admin_can_update_documento(self, mock_storage_save):
        self.client.force_login(self.admin)
        doc = Documento.objects.create(
            numero="Res. 50/2024",
            titulo="Título Original",
            categoria=Documento.Categoria.RESOLUCION,
            descripcion="Descripción Original",
            archivo_almacenado=SimpleUploadedFile("doc_orig.pdf", b"%PDF-1.4 ..."),
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )

        update_url = reverse("documents:documento_edit", kwargs={"pk": doc.pk})
        data = {
            "numero": "Res. 50/2024",
            "titulo": "Título Modificado",
            "categoria": Documento.Categoria.ESTATUTO,
            "fecha_documento": "2024-06-01",
            "descripcion": "Descripción Actualizada",
            "visibilidad": Documento.Visibilidad.PUBLICO,
            "vigente": False,
        }
        response = self.client.post(update_url, data)
        self.assertEqual(response.status_code, 302)

        doc.refresh_from_db()
        self.assertEqual(doc.titulo, "Título Modificado")
        self.assertEqual(doc.categoria, Documento.Categoria.ESTATUTO)
        self.assertFalse(doc.vigente)
        self.assertEqual(doc.modificado_por, self.admin)

    def test_admin_can_toggle_vigente(self):
        self.client.force_login(self.admin)
        doc = Documento.objects.create(
            numero="Res. 60/2024",
            titulo="Resolución de Prueba",
            categoria=Documento.Categoria.RESOLUCION,
            descripcion="Para alternar vigencia",
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )

        toggle_url = reverse("documents:documento_toggle_vigente", kwargs={"pk": doc.pk})
        self.client.post(toggle_url)

        doc.refresh_from_db()
        self.assertFalse(doc.vigente)

        self.client.post(toggle_url)
        doc.refresh_from_db()
        self.assertTrue(doc.vigente)

    @patch("core.storage.SupabaseStorage._save", return_value="documentos/doc_del.pdf")
    @patch("core.storage.SupabaseStorage.delete")
    def test_admin_can_delete_documento_and_triggers_signal(self, mock_storage_delete, mock_storage_save):
        self.client.force_login(self.admin)
        doc = Documento.objects.create(
            numero="Res. 70/2024",
            titulo="Resolución para Eliminar",
            categoria=Documento.Categoria.RESOLUCION,
            descripcion="Para borrar",
            archivo_almacenado=SimpleUploadedFile("doc_del.pdf", b"%PDF-1.4 ..."),
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )

        delete_url = reverse("documents:documento_delete", kwargs={"pk": doc.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Documento.objects.filter(pk=doc.pk).exists())
        # Verificar que la señal intentó limpiar el archivo en Supabase
        mock_storage_delete.assert_called()

    @patch("core.storage.SupabaseStorage._save", return_value="documentos/sin_numero_ni_desc.pdf")
    def test_admin_can_create_documento_without_numero_and_descripcion(self, mock_storage_save):
        self.client.force_login(self.admin)
        url = reverse("documents:documento_create")
        pdf_file = SimpleUploadedFile("form_tramite.pdf", b"%PDF-1.4 test content", content_type="application/pdf")

        data = {
            "numero": "",
            "titulo": "Formulario de Solicitud de Trámite",
            "categoria": Documento.Categoria.MODELO,
            "fecha_documento": "",
            "descripcion": "",
            "archivo_almacenado": pdf_file,
            "visibilidad": Documento.Visibilidad.PUBLICO,
            "vigente": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('accounts:dashboard')}?tab=admin_documentos")

        doc = Documento.objects.filter(titulo="Formulario de Solicitud de Trámite").first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.numero, "")
        self.assertEqual(doc.descripcion, "")
        self.assertEqual(str(doc), "Formulario de Solicitud de Trámite")


class DocumentoFileValidationTests(TestCase):
    def test_validador_rechaza_archivos_ejecutables(self):
        from apps.documents.validators import validate_document_file
        from django.core.exceptions import ValidationError
        bad_file = SimpleUploadedFile("peligroso.exe", b"MZ...", content_type="application/x-msdownload")
        with self.assertRaises(ValidationError) as ctx:
            validate_document_file(bad_file)
        self.assertIn("Solo se permiten archivos en formato PDF", str(ctx.exception))

    def test_validador_rechaza_extensiones_no_permitidas(self):
        from apps.documents.validators import validate_document_file
        from django.core.exceptions import ValidationError
        for ext in ["script.py", "foto.png", "datos.zip"]:
            bad_file = SimpleUploadedFile(ext, b"contenido dummy", content_type="application/octet-stream")
            with self.assertRaises(ValidationError):
                validate_document_file(bad_file)

    def test_validador_acepta_pdf_y_word(self):
        from apps.documents.validators import validate_document_file
        pdf_file = SimpleUploadedFile("resolucion.pdf", b"%PDF-1.4...", content_type="application/pdf")
        docx_file = SimpleUploadedFile("convenio.docx", b"PK...", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_file = SimpleUploadedFile("estatuto.doc", b"\xd0\xcf\x11\xe0...", content_type="application/msword")

        # No deben lanzar excepción
        validate_document_file(pdf_file)
        validate_document_file(docx_file)
        validate_document_file(doc_file)

    def test_validador_rechaza_archivos_superiores_a_10mb(self):
        from apps.documents.validators import validate_document_file
        from django.core.exceptions import ValidationError
        oversized_file = SimpleUploadedFile("gigante.pdf", b"a" * 100, content_type="application/pdf")
        oversized_file.size = 11 * 1024 * 1024  # 11 MB
        with self.assertRaises(ValidationError) as ctx:
            validate_document_file(oversized_file)
        self.assertIn("no puede superar los 10 MB", str(ctx.exception))


class DocumentoPublicListFilterTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_doc_filters",
            password="AdminPassword123!",
            must_change_password=False,
        )
        self.doc1 = Documento.objects.create(
            titulo="Estatuto Social Reformado",
            numero="Ley 4118",
            categoria=Documento.Categoria.ESTATUTO,
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )
        self.doc2 = Documento.objects.create(
            titulo="Resolución de Directorio Anual",
            numero="Res 10/2026",
            categoria=Documento.Categoria.RESOLUCION,
            visibilidad=Documento.Visibilidad.PUBLICO,
            vigente=True,
            creado_por=self.admin,
        )

    def test_filtro_por_categoria_en_listado(self):
        url = reverse("documents:documento_list")
        response = self.client.get(url, {"categoria": Documento.Categoria.ESTATUTO})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estatuto Social Reformado")
        self.assertNotContains(response, "Resolución de Directorio Anual")

    def test_busqueda_por_texto_en_listado(self):
        url = reverse("documents:documento_list")
        response = self.client.get(url, {"q": "Reformado"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estatuto Social Reformado")
        self.assertNotContains(response, "Resolución de Directorio Anual")


