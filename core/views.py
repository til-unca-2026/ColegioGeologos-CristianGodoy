from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from apps.content.models import Contenido


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
            es_staff = user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores"]).exists()
            if not es_staff:
                base_qs = base_qs.filter(
                    visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS]
                )

        # 1. Novedades y Noticias recientes (excluyendo Eventos y Capacitaciones)
        noticias_qs = (
            base_qs.exclude(tipo__in=[Contenido.Tipo.EVENTO, Contenido.Tipo.CAPACITACION])
            .order_by("-destacado", "-fecha_publicacion")[:2]
        )

        # 2. Próximos Eventos y Capacitaciones
        eventos_qs = (
            base_qs.filter(tipo__in=[Contenido.Tipo.EVENTO, Contenido.Tipo.CAPACITACION])
            .select_related("detalle_evento")
            .order_by("detalle_evento__inicio", "-fecha_publicacion")[:2]
        )

        context["home_noticias"] = noticias_qs
        context["home_eventos"] = eventos_qs
        return context


def site_under_construction(request):
    return render(request, "site_under_construction.html")


def error_404(request, exception):
    return render(request, "error404.html", status=404)


def error_500(request):
    return render(request, "error500.html", status=500)
