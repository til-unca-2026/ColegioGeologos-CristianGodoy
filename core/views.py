from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from apps.content.models import Contenido
from apps.documents.models import Documento
from apps.directory.models import Matriculado, Especialidad


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        user = self.request.user

        # Base para publicaciones activas
        base_qs = Contenido.objects.filter(
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            fecha_publicacion__lte=now,
        ).select_related("creado_por").prefetch_related("imagenes")

        # Filtrar por visibilidad según sesión
        if not user.is_authenticated:
            base_qs = base_qs.filter(visibilidad=Contenido.Visibilidad.PUBLICO)
        else:
            es_staff = user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
            if not es_staff:
                base_qs = base_qs.filter(
                    visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS]
                )

        # 1. Novedades y Noticias recientes (excluyendo Capacitaciones, Beneficios y Convocatorias)
        noticias_qs = (
            base_qs.exclude(tipo__in=[
                Contenido.Tipo.CAPACITACION,
                Contenido.Tipo.BENEFICIO,
                Contenido.Tipo.CONVOCATORIA,
            ])
            .order_by("-fecha_publicacion")[:2]
        )

        # 2. Próximas Capacitaciones
        eventos_qs = (
            base_qs.filter(tipo=Contenido.Tipo.CAPACITACION)
            .select_related("detalle_evento")
            .order_by("detalle_evento__inicio", "-fecha_publicacion")[:2]
        )

        # 3. Documentos Oficiales vigentes y accesibles
        doc_qs = Documento.objects.filter(vigente=True)
        if not user.is_authenticated:
            doc_qs = doc_qs.filter(visibilidad=Documento.Visibilidad.PUBLICO)
        else:
            es_staff = user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
            if not es_staff:
                doc_qs = doc_qs.filter(visibilidad__in=[Documento.Visibilidad.PUBLICO, Documento.Visibilidad.MATRICULADOS])

        documentos_recientes = doc_qs.order_by("-fecha_documento", "-fecha_creacion")[:3]

        context["home_noticias"] = noticias_qs
        context["home_eventos"] = eventos_qs
        context["home_documentos"] = documentos_recientes

        # Especialidades dinámicas para enlace con filtro al Directorio
        context["home_especialidades"] = Especialidad.objects.all().order_by("nombre")

        # Métrica de matriculados registrados
        context["total_matriculados"] = Matriculado.objects.count()

        return context


class QuienesSomosView(TemplateView):
    template_name = "quienes_somos.html"


class ServiciosProfesionalesView(TemplateView):
    """
    Vista informativa sobre servicios profesionales (RF-06):
    Constancias, visados técnicos y tablas de aranceles oficiales en PDF.
    """
    template_name = "servicios_profesionales.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        doc_qs = Documento.objects.filter(
            vigente=True,
            categoria=Documento.Categoria.ARANCEL
        )

        if not user.is_authenticated:
            doc_qs = doc_qs.filter(visibilidad=Documento.Visibilidad.PUBLICO)
        else:
            es_staff = user.is_superuser or user.groups.filter(
                name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]
            ).exists()
            if not es_staff:
                doc_qs = doc_qs.filter(
                    visibilidad__in=[Documento.Visibilidad.PUBLICO, Documento.Visibilidad.MATRICULADOS]
                )

        context["documentos_aranceles"] = doc_qs.order_by("-fecha_documento", "-fecha_creacion")
        return context


class ConveniosView(TemplateView):
    """
    Vista dedicada para Beneficios para matriculados (RF-06).
    Muestra publicaciones vigentes de acuerdos comerciales, descuentos y beneficios.
    """
    template_name = "convenios.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        user = self.request.user

        # Publicaciones de beneficios directos para matriculados
        base_qs = Contenido.objects.filter(
            tipo=Contenido.Tipo.BENEFICIO,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            fecha_publicacion__lte=now,
        ).select_related("creado_por")

        if not user.is_authenticated:
            base_qs = base_qs.filter(visibilidad=Contenido.Visibilidad.PUBLICO)
        else:
            es_staff = user.is_superuser or user.groups.filter(
                name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]
            ).exists()
            if not es_staff:
                base_qs = base_qs.filter(
                    visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS]
                )

        context["convenios"] = base_qs.order_by("-fecha_publicacion")
        return context


class ConvocatoriasLaboralesView(TemplateView):
    """
    Vista dedicada para Convocatorias y Oportunidades Laborales (RF-06).
    Muestra difusión de búsquedas profesionales para geólogos en la región.
    """
    template_name = "convocatorias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        user = self.request.user

        base_qs = Contenido.objects.filter(
            tipo=Contenido.Tipo.CONVOCATORIA,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            fecha_publicacion__lte=now,
        ).select_related("creado_por")

        if not user.is_authenticated:
            base_qs = base_qs.filter(visibilidad=Contenido.Visibilidad.PUBLICO)
        else:
            es_staff = user.is_superuser or user.groups.filter(
                name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]
            ).exists()
            if not es_staff:
                base_qs = base_qs.filter(
                    visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS]
                )

        context["convocatorias"] = base_qs.order_by("-fecha_publicacion")
        return context


class BeneficiosMatriculadosView(TemplateView):
    """
    Vista retrocompatible para /beneficios/, redirige o renderiza convenios por defecto.
    """
    template_name = "convenios.html"

    def get(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        return redirect("convenios")




def site_under_construction(request):
    return render(request, "site_under_construction.html")


def error_404(request, exception):
    return render(request, "error404.html", status=404)


def error_500(request):
    return render(request, "error500.html", status=500)
