from urllib.parse import urlparse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ContenidoForm, DetalleEventoForm
from .models import Contenido, DetalleEvento, ImagenContenido


class ContentPermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Permite acceso a administradores, colaboradores o usuarios con permisos de contenido.
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
            or user.has_perm("content.add_contenido")
            or user.has_perm("content.change_contenido")
        )

    def handle_no_permission(self):
        messages.error(self.request, "No tenés permisos para gestionar contenidos.")
        return redirect("accounts:dashboard")


# =====================================================================
# Vistas Públicas / Matriculados (Listado y Detalle)
# =====================================================================

class NovedadesListView(ListView):
    model = Contenido
    template_name = "content/novedades_list.html"
    context_object_name = "novedades"
    paginate_by = 10

    # Tipos que cuentan con su propia sección y plantilla exclusiva
    TIPOS_EXCLUIDOS = [
        Contenido.Tipo.CAPACITACION,
        Contenido.Tipo.BENEFICIO,
        Contenido.Tipo.CONVOCATORIA,
    ]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        # En la sección pública de Novedades NUNCA se muestran borradores ni programados
        # Solo contenidos efectivamente publicados cuya fecha ya haya llegado
        qs = Contenido.objects.filter(
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            fecha_publicacion__lte=now,
        ).exclude(
            tipo__in=self.TIPOS_EXCLUIDOS
        ).select_related("creado_por").prefetch_related("imagenes", "detalle_evento")

        # Reglas de visibilidad:
        # Colaboradores y administradores ven contenidos públicos, de matriculados e internos
        es_staff = user.is_authenticated and (
            user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
        )

        if not es_staff:
            if user.is_authenticated:
                # Matriculado / usuario estándar: ve PUBLICO y MATRICULADOS
                qs = qs.filter(visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS])
            else:
                # Visitante anónimo: solo PUBLICO
                qs = qs.filter(visibilidad=Contenido.Visibilidad.PUBLICO)

        # Filtro por tipo (solo entre los tipos válidos para esta sección)
        tipo = self.request.GET.get("tipo", "").strip()
        tipos_validos = [choice[0] for choice in self.get_tipos_disponibles()]
        if tipo and tipo in tipos_validos:
            qs = qs.filter(tipo=tipo)

        # Búsqueda por texto (título, resumen, cuerpo)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(titulo__icontains=q) | Q(resumen__icontains=q) | Q(cuerpo__icontains=q)
            )

        return qs.order_by("-fecha_publicacion", "-fecha_creacion")

    def get_tipos_disponibles(self):
        return [
            choice for choice in Contenido.Tipo.choices
            if choice[0] not in self.TIPOS_EXCLUIDOS
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipo_actual"] = self.request.GET.get("tipo", "")
        context["q"] = self.request.GET.get("q", "")
        context["tipos_disponibles"] = self.get_tipos_disponibles()
        context["total_publicaciones"] = self.get_queryset().count()
        return context


class CapacitacionesListView(ListView):
    """
    Vista dedicada para la Sección 'Capacitaciones' (RF-04, RF-06, CU-04).
    Muestra exclusivamente cursos, talleres y jornadas profesionales con enlace de inscripción externo.
    """
    model = Contenido
    template_name = "content/capacitaciones_list.html"
    context_object_name = "capacitaciones"
    paginate_by = 9

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        qs = Contenido.objects.filter(
            tipo=Contenido.Tipo.CAPACITACION,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            fecha_publicacion__lte=now,
        ).select_related("creado_por", "detalle_evento").prefetch_related("imagenes")

        es_staff = user.is_authenticated and (
            user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
        )

        if not es_staff:
            if user.is_authenticated:
                qs = qs.filter(visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS])
            else:
                qs = qs.filter(visibilidad=Contenido.Visibilidad.PUBLICO)

        # Búsqueda opcional
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(titulo__icontains=q) | Q(resumen__icontains=q) | Q(cuerpo__icontains=q) | Q(detalle_evento__lugar__icontains=q)
            )

        # Ordenar primero los próximos eventos por fecha de inicio, o por fecha de publicación
        return qs.order_by("-detalle_evento__inicio", "-fecha_publicacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["total_capacitaciones"] = self.get_queryset().count()
        context["now"] = timezone.now()
        return context


class NovedadDetailView(DetailView):
    model = Contenido
    template_name = "content/novedad_detail.html"
    context_object_name = "novedad"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("slug")
        pk = self.kwargs.get("pk")

        user = self.request.user
        now = timezone.now()

        qs = Contenido.objects.select_related("creado_por").prefetch_related("imagenes", "detalle_evento")

        if slug:
            obj = get_object_or_404(qs, slug=slug)
        else:
            obj = get_object_or_404(qs, pk=pk)

        # Validación de permisos para ver la nota:
        es_staff = user.is_authenticated and (
            user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists()
        )
        if not es_staff:
            # Si no está publicada o la fecha no llegó
            if obj.estado_publicacion != Contenido.EstadoPublicacion.PUBLICADO or (obj.fecha_publicacion and obj.fecha_publicacion > now):
                raise Http404("La publicación no está disponible.")

            # Validación según visibilidad
            if obj.visibilidad == Contenido.Visibilidad.INTERNO:
                raise Http404("No tenés permiso para ver este contenido institucional.")
            elif obj.visibilidad == Contenido.Visibilidad.MATRICULADOS and not user.is_authenticated:
                messages.info(self.request, "Esta publicación es exclusiva para matriculados. Iniciá sesión para acceder.")
                raise Http404("Contenido exclusivo para matriculados.")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        novedad = self.object
        context["portada"] = novedad.imagen_portada
        context["otras_imagenes"] = novedad.imagenes.exclude(id=getattr(novedad.imagen_portada, "id", None))

        # Determinar el botón de retorno contextual según de dónde vino el usuario (HTTP_REFERER)
        referer = self.request.META.get("HTTP_REFERER", "")
        host = self.request.get_host()
        volver_url = None
        volver_texto = None

        if referer and host in referer:
            try:
                parsed_ref = urlparse(referer)
                ref_path = parsed_ref.path
                full_ref = referer

                # 1. Vino de Capacitaciones
                if ref_path.startswith(reverse("content:capacitaciones_list")):
                    volver_url = full_ref
                    volver_texto = "Volver a Capacitaciones"
                # 2. Vino de Noticias
                elif ref_path.startswith(reverse("content:novedades_list")):
                    volver_url = full_ref
                    volver_texto = "Volver a Noticias"
                # 3. Vino de Beneficios
                elif ref_path.startswith(reverse("beneficios")):
                    volver_url = full_ref
                    volver_texto = "Volver a Beneficios"
                # 4. Vino de Bolsa de Trabajo (Convocatorias)
                elif ref_path.startswith(reverse("convocatorias")):
                    volver_url = full_ref
                    volver_texto = "Volver a Bolsa de Trabajo"
                # 5. Vino del Inicio
                elif ref_path == reverse("home") or ref_path == "/":
                    volver_url = reverse("home")
                    volver_texto = "Volver al Inicio"
            except Exception:
                pass

        # Fallback coherente si entró directo (WhatsApp, pestaña nueva, email, etc.)
        if not volver_url:
            if novedad.tipo == Contenido.Tipo.CAPACITACION:
                volver_url = reverse("content:capacitaciones_list")
                volver_texto = "Volver a Capacitaciones"
            elif novedad.tipo == Contenido.Tipo.BENEFICIO:
                volver_url = reverse("beneficios")
                volver_texto = "Volver a Beneficios"
            elif novedad.tipo == Contenido.Tipo.CONVOCATORIA:
                volver_url = reverse("convocatorias")
                volver_texto = "Volver a Bolsa de Trabajo"
            else:
                volver_url = reverse("content:novedades_list")
                volver_texto = "Volver a Noticias"

        context["volver_url"] = volver_url
        context["volver_texto"] = volver_texto

        # Publicaciones recientes sugeridas: estrictamente del MISMO tipo que el contenido actual
        now = timezone.now()
        user = self.request.user

        relacionadas_qs = Contenido.objects.filter(
            tipo=novedad.tipo,
            estado_publicacion=Contenido.EstadoPublicacion.PUBLICADO,
            fecha_publicacion__lte=now,
        ).exclude(pk=novedad.pk)

        # Filtrar por visibilidad según autenticación
        if not (user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=["administradores", "colaboradores", "Administradores", "Colaboradores"]).exists())):
            if user.is_authenticated:
                relacionadas_qs = relacionadas_qs.filter(visibilidad__in=[Contenido.Visibilidad.PUBLICO, Contenido.Visibilidad.MATRICULADOS])
            else:
                relacionadas_qs = relacionadas_qs.filter(visibilidad=Contenido.Visibilidad.PUBLICO)

        # Si tiene fecha de evento/inicio, ordenar cronológicamente
        if novedad.tipo in [Contenido.Tipo.EVENTO, Contenido.Tipo.CAPACITACION]:
            relacionadas = relacionadas_qs.order_by("-detalle_evento__inicio", "-fecha_publicacion")[:3]
        else:
            relacionadas = relacionadas_qs.order_by("-fecha_publicacion")[:3]

        # Título contextual de sugerencias según el tipo exacto
        titulos_por_tipo = {
            Contenido.Tipo.NOTICIA: "Otras noticias recientes",
            Contenido.Tipo.COMUNICADO: "Otros comunicados oficiales",
            Contenido.Tipo.EVENTO: "Otros eventos",
            Contenido.Tipo.CAPACITACION: "Otras capacitaciones",
            Contenido.Tipo.BENEFICIO: "Otros beneficios",
            Contenido.Tipo.CONVOCATORIA: "Otras convocatorias laborales",
        }
        titulo_relacionadas = titulos_por_tipo.get(novedad.tipo, f"Más publicaciones de {novedad.get_tipo_display().lower()}")

        context["relacionadas"] = relacionadas
        context["titulo_relacionadas"] = titulo_relacionadas
        return context


# =====================================================================
# Vistas de Gestión y Formulario (Colaboradores y Administradores)
# =====================================================================

class ContenidoCreateView(ContentPermissionRequiredMixin, CreateView):
    model = Contenido
    form_class = ContenidoForm
    template_name = "content/contenido_form.html"
    success_url = reverse_lazy("accounts:dashboard")

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=contenidos"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["evento_form"] = DetalleEventoForm(self.request.POST, prefix="evento")
        else:
            context["evento_form"] = DetalleEventoForm(prefix="evento")
        context["is_create"] = True
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        evento_form = context["evento_form"]
        tipo = form.cleaned_data.get("tipo")
        requiere_evento = tipo in [
            Contenido.Tipo.EVENTO,
            Contenido.Tipo.CAPACITACION,
        ]

        if requiere_evento and not evento_form.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            contenido = form.save(commit=False)
            contenido.creado_por = self.request.user
            contenido.save()

            if requiere_evento:
                detalle = evento_form.save(commit=False)
                detalle.contenido = contenido
                detalle.save()

            # Guardar imagen de portada si se proporcionó
            imagen_file = form.cleaned_data.get("imagen_portada")
            if imagen_file:
                epigrafe = form.cleaned_data.get("epigrafe_portada") or ""
                ImagenContenido.objects.create(
                    contenido=contenido,
                    imagen=imagen_file,
                    epigrafe=epigrafe,
                    es_portada=True,
                    orden=0,
                )

            # Guardar imágenes adicionales de galería
            archivos_galeria = self.request.FILES.getlist("imagenes_galeria")
            for idx, img_galeria in enumerate(archivos_galeria, start=1):
                ImagenContenido.objects.create(
                    contenido=contenido,
                    imagen=img_galeria,
                    epigrafe="",
                    es_portada=False,
                    orden=idx,
                )

        messages.success(self.request, f"Contenido «{contenido.titulo}» creado con éxito.")
        return redirect(self.get_success_url())


class ContenidoUpdateView(ContentPermissionRequiredMixin, UpdateView):
    model = Contenido
    form_class = ContenidoForm
    template_name = "content/contenido_form.html"

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=contenidos"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contenido = self.object
        detalle_evento = getattr(contenido, "detalle_evento", None)

        if self.request.POST:
            context["evento_form"] = DetalleEventoForm(
                self.request.POST,
                instance=detalle_evento,
                prefix="evento",
            )
        else:
            context["evento_form"] = DetalleEventoForm(
                instance=detalle_evento,
                prefix="evento",
            )

        context["is_create"] = False
        context["portada_actual"] = contenido.imagenes.filter(es_portada=True).first()
        context["galeria_actual"] = contenido.imagenes.filter(es_portada=False).order_by("orden", "id")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        evento_form = context["evento_form"]
        tipo = form.cleaned_data.get("tipo")
        requiere_evento = tipo in [
            Contenido.Tipo.EVENTO,
            Contenido.Tipo.CAPACITACION,
        ]

        if requiere_evento and not evento_form.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            contenido = form.save(commit=False)
            contenido.modificado_por = self.request.user
            contenido.save()

            if requiere_evento:
                detalle = evento_form.save(commit=False)
                detalle.contenido = contenido
                detalle.save()
            elif hasattr(contenido, "detalle_evento"):
                contenido.detalle_evento.delete()

            imagen_file = form.cleaned_data.get("imagen_portada")
            epigrafe = form.cleaned_data.get("epigrafe_portada") or ""
            portada_existente = contenido.imagenes.filter(es_portada=True).first()

            if imagen_file:
                if portada_existente:
                    portada_existente.imagen = imagen_file
                    portada_existente.epigrafe = epigrafe
                    portada_existente.save()
                else:
                    ImagenContenido.objects.create(
                        contenido=contenido,
                        imagen=imagen_file,
                        epigrafe=epigrafe,
                        es_portada=True,
                        orden=0,
                    )
            elif portada_existente:
                # Si no subió una nueva imagen pero editó el epígrafe
                portada_existente.epigrafe = epigrafe
                portada_existente.save()

            # Agregar nuevas imágenes a la galería si se seleccionaron
            archivos_galeria = self.request.FILES.getlist("imagenes_galeria")
            max_orden = contenido.imagenes.filter(es_portada=False).count()
            for idx, img_galeria in enumerate(archivos_galeria, start=max_orden + 1):
                ImagenContenido.objects.create(
                    contenido=contenido,
                    imagen=img_galeria,
                    epigrafe="",
                    es_portada=False,
                    orden=idx,
                )

        messages.success(self.request, f"Contenido «{contenido.titulo}» actualizado.")
        return redirect(self.get_success_url())


class ContenidoDeleteView(ContentPermissionRequiredMixin, DeleteView):
    model = Contenido

    def get_success_url(self):
        return f"{reverse_lazy('accounts:dashboard')}?tab=contenidos"

    def delete(self, request, *args, **kwargs):
        contenido = self.get_object()
        titulo = contenido.titulo
        contenido.delete()
        messages.success(request, f"El contenido «{titulo}» fue eliminado correctamente.")
        return redirect(self.get_success_url())


class ImagenContenidoDeleteView(ContentPermissionRequiredMixin, View):
    """
    Elimina una imagen individual de la galería desde el formulario de edición.
    """
    def post(self, request, pk, *args, **kwargs):
        imagen = get_object_or_404(ImagenContenido, pk=pk)
        contenido_id = imagen.contenido_id
        imagen.delete()  # La señal post_delete limpiará el archivo en Supabase Storage
        messages.success(request, "Imagen de la galería eliminada.")
        return redirect("content:contenido_edit", pk=contenido_id)


class ContenidoToggleEstadoView(ContentPermissionRequiredMixin, View):
    """
    Permite alternar rápidamente entre Borrador (pausa) y Publicado (fecha actual) desde el dashboard.
    """
    def post(self, request, pk, *args, **kwargs):
        contenido = get_object_or_404(Contenido, pk=pk)
        if contenido.estado_publicacion in [Contenido.EstadoPublicacion.PUBLICADO, Contenido.EstadoPublicacion.PROGRAMADO]:
            contenido.fecha_publicacion = None
            contenido.estado_publicacion = Contenido.EstadoPublicacion.BORRADOR
            nuevo_estado = "Borrador (pausado)"
        else:
            contenido.fecha_publicacion = timezone.now()
            contenido.estado_publicacion = Contenido.EstadoPublicacion.PUBLICADO
            nuevo_estado = "Publicado"

        contenido.modificado_por = request.user
        contenido.save(update_fields=["estado_publicacion", "fecha_publicacion", "modificado_por"])
        messages.success(request, f"«{contenido.titulo}» ahora está en estado {nuevo_estado}.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=contenidos")
