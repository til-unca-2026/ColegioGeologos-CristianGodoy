from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View
from .forms import (
    MatriculadoForm,
    TituloForm,
    HistorialEstadoMatriculaForm,
    AntecedenteDisciplinarioForm,
    EspecialidadForm,
    UniversidadForm,
)
from .models import (
    Matriculado,
    Titulo,
    HistorialEstadoMatricula,
    AntecedenteDisciplinario,
    Especialidad,
    Universidad,
)


class MatriculadoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para dar de alta una nueva matrícula vinculada a un usuario.
    Permite cargar el Título Universitario habilitante en el mismo formulario.
    Al crearse, genera atómicamente:
    1. El registro del Matriculado.
    2. El Título Universitario con su diploma.
    3. El primer registro de HistorialEstadoMatricula en estado ACTIVA.
    """
    permission_required = "directory.add_matriculado"
    model = Matriculado
    form_class = MatriculadoForm
    template_name = "directory/matriculado_form.html"

    def get_success_url(self):
        return reverse_lazy("directory:matriculado_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        context["title"] = "Registrar nuevo Matriculado"
        if "titulo_form" not in context:
            if self.request.POST:
                context["titulo_form"] = TituloForm(self.request.POST, self.request.FILES, prefix="titulo")
            else:
                context["titulo_form"] = TituloForm(prefix="titulo")
        context["especialidad_form"] = EspecialidadForm()
        context["universidad_form"] = UniversidadForm()

        # Mapeo de usuario ID -> Nombre completo para actualización dinámica del label
        from django.contrib.auth import get_user_model
        User = get_user_model()
        usuarios_qs = User.objects.all()
        context["usuarios_nombres_json"] = {
            str(u.id): (u.get_full_name() or u.username) for u in usuarios_qs
        }
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        titulo_form = TituloForm(request.POST, request.FILES, prefix="titulo")

        if form.is_valid() and titulo_form.is_valid():
            return self.form_valid(form, titulo_form)
        else:
            return self.form_invalid(form, titulo_form)

    def form_valid(self, form, titulo_form):
        with transaction.atomic():
            matriculado = form.save(commit=False)
            matriculado.creado_por = self.request.user
            matriculado.save()
            form.save_m2m()

            # Guardar el título universitario vinculado al nuevo matriculado
            titulo = titulo_form.save(commit=False)
            titulo.matriculado = matriculado
            titulo.creado_por = self.request.user
            titulo.save()

            # Generar estado inicial ACTIVA automáticamente
            HistorialEstadoMatricula.objects.create(
                matriculado=matriculado,
                estado=HistorialEstadoMatricula.Estado.ACTIVA,
                fecha_desde=matriculado.fecha_matriculacion,
                motivo="Alta inicial en el padrón de matriculados",
                resolucion_acta=f"Libro {matriculado.libro} Folio {matriculado.folio}",
                creado_por=self.request.user,
            )

        messages.success(
            self.request,
            f"Matrícula N° {matriculado.numero_matricula} y título '{titulo.denominacion}' registrados exitosamente.",
        )
        self.object = matriculado
        return redirect(self.get_success_url())

    def form_invalid(self, form, titulo_form):
        return self.render_to_response(
            self.get_context_data(form=form, titulo_form=titulo_form)
        )


class MatriculadoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para editar los datos de un matriculado (matrícula, libro/folio, domicilio profesional).
    """
    permission_required = "directory.change_matriculado"
    model = Matriculado
    form_class = MatriculadoForm
    template_name = "directory/matriculado_form.html"

    def get_success_url(self):
        return reverse_lazy("directory:matriculado_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        matriculado = form.save(commit=False)
        matriculado.modificado_por = self.request.user
        matriculado.save()
        form.save_m2m()
        messages.success(
            self.request,
            f"Datos del matriculado N° {matriculado.numero_matricula} actualizados correctamente.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context["title"] = f"Editar Matrícula N° {self.object.numero_matricula}"
        context["especialidad_form"] = EspecialidadForm()
        context["universidad_form"] = UniversidadForm()
        return context


class MatriculadoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Ficha completa de un matriculado: títulos, historial de estados y antecedentes disciplinarios.
    """
    permission_required = "directory.view_matriculado"
    model = Matriculado
    template_name = "directory/matriculado_detail.html"
    context_object_name = "matriculado"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matriculado = self.object
        context["titulos"] = matriculado.titulos.select_related("emitido_por").all()
        context["estados"] = matriculado.estados.select_related("origen_sancion").order_by("-fecha_desde", "-fecha_creacion")
        context["antecedentes"] = matriculado.antecedentes.all().order_by("-fecha_resolucion")
        context["titulo_form"] = TituloForm()
        context["estado_form"] = HistorialEstadoMatriculaForm(matriculado=matriculado)
        context["antecedente_form"] = AntecedenteDisciplinarioForm()
        context["universidad_form"] = UniversidadForm()
        return context


class TituloCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Crea un nuevo título asociado a un matriculado.
    """
    permission_required = "directory.add_titulo"
    model = Titulo
    form_class = TituloForm

    def form_valid(self, form):
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        titulo = form.save(commit=False)
        titulo.matriculado = matriculado
        titulo.creado_por = self.request.user
        titulo.save()
        messages.success(self.request, f"Título '{titulo.denominacion}' agregado con éxito.")
        return redirect("directory:matriculado_detail", pk=matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el título. Por favor revise los campos.")
        return redirect("directory:matriculado_detail", pk=self.kwargs["matriculado_id"])


class TituloUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Edita un título existente de un matriculado para subsanar errores de tipeo o fechas.
    """
    permission_required = "directory.change_titulo"
    model = Titulo
    form_class = TituloForm

    def form_valid(self, form):
        titulo = form.save(commit=False)
        titulo.modificado_por = self.request.user
        titulo.save()
        messages.success(self.request, f"Título '{titulo.denominacion}' actualizado correctamente.")
        return redirect("directory:matriculado_detail", pk=titulo.matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el título. Por favor revise los campos.")
        return redirect("directory:matriculado_detail", pk=self.object.matriculado.pk)


class HistorialEstadoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Registra un cambio de estado en la matrícula (ej. SUSPENDIDA, ACTIVA, BAJA).
    """
    permission_required = "directory.add_historialestadomatricula"
    model = HistorialEstadoMatricula
    form_class = HistorialEstadoMatriculaForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        kwargs["matriculado"] = matriculado
        return kwargs

    def form_valid(self, form):
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        estado = form.save(commit=False)
        estado.matriculado = matriculado
        estado.creado_por = self.request.user
        estado.save()
        messages.success(
            self.request,
            f"Nuevo estado '{estado.get_estado_display()}' registrado para la matrícula.",
        )
        return redirect("directory:matriculado_detail", pk=matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el cambio de estado. Por favor revise las fechas y campos.")
        return redirect("directory:matriculado_detail", pk=self.kwargs["matriculado_id"])


class HistorialEstadoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Edita un registro del historial de estado para subsanar errores de tipeo, fechas o actas.
    """
    permission_required = "directory.change_historialestadomatricula"
    model = HistorialEstadoMatricula
    form_class = HistorialEstadoMatriculaForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["matriculado"] = self.object.matriculado
        return kwargs

    def form_valid(self, form):
        estado = form.save(commit=False)
        estado.modificado_por = self.request.user
        estado.save()
        messages.success(self.request, f"Registro de estado '{estado.get_estado_display()}' actualizado correctamente.")
        return redirect("directory:matriculado_detail", pk=estado.matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el estado de matrícula.")
        return redirect("directory:matriculado_detail", pk=self.object.matriculado.pk)


class AntecedenteDisciplinarioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Registra un antecedente disciplinario o sanción contra un matriculado.
    """
    permission_required = "directory.add_antecedentedisciplinario"
    model = AntecedenteDisciplinario
    form_class = AntecedenteDisciplinarioForm

    def form_valid(self, form):
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        antecedente = form.save(commit=False)
        antecedente.matriculado = matriculado
        antecedente.creado_por = self.request.user
        antecedente.save()
        messages.success(
            self.request,
            f"Antecedente disciplinario Exp. {antecedente.numero_expediente} registrado.",
        )
        return redirect("directory:matriculado_detail", pk=matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el antecedente disciplinario.")
        return redirect("directory:matriculado_detail", pk=self.kwargs["matriculado_id"])


class AntecedenteDisciplinarioUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Edita un antecedente disciplinario para subsanar errores de tipeo, montos o expedientes.
    """
    permission_required = "directory.change_antecedentedisciplinario"
    model = AntecedenteDisciplinario
    form_class = AntecedenteDisciplinarioForm

    def form_valid(self, form):
        antecedente = form.save(commit=False)
        antecedente.modificado_por = self.request.user
        antecedente.save()
        messages.success(self.request, f"Antecedente Exp. {antecedente.numero_expediente} actualizado correctamente.")
        return redirect("directory:matriculado_detail", pk=antecedente.matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el antecedente disciplinario.")
        return redirect("directory:matriculado_detail", pk=self.object.matriculado.pk)


class EspecialidadCreateAjaxView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Crea una nueva Especialidad vía AJAX (ej. desde el modal en el formulario de matriculado)
    y retorna su ID y nombre para agregarla y seleccionarla en caliente en el select sin recargar.
    """
    permission_required = "directory.add_especialidad"

    def post(self, request, *args, **kwargs):
        form = EspecialidadForm(request.POST)
        if form.is_valid():
            especialidad = form.save()
            return JsonResponse({
                "success": True,
                "id": especialidad.id,
                "nombre": especialidad.nombre,
                "message": f"Especialidad '{especialidad.nombre}' creada con éxito.",
            })
        
        errors = [f"{field}: {err[0]}" for field, err in form.errors.items()]
        return JsonResponse({
            "success": False,
            "error": " / ".join(errors) or "Error al validar la especialidad.",
        }, status=400)


class UniversidadCreateAjaxView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Crea una nueva Universidad vía AJAX y retorna ID, nombre y sigla
    para agregarla al selector de universidades en caliente.
    """
    permission_required = "directory.add_universidad"

    def post(self, request, *args, **kwargs):
        form = UniversidadForm(request.POST)
        if form.is_valid():
            universidad = form.save()
            nombre_display = f"{universidad.nombre} ({universidad.sigla})" if universidad.sigla else universidad.nombre
            return JsonResponse({
                "success": True,
                "id": universidad.id,
                "nombre": nombre_display,
                "message": f"Universidad '{universidad.nombre}' creada con éxito.",
            })

        errors = [f"{field}: {err[0]}" for field, err in form.errors.items()]
        return JsonResponse({
            "success": False,
            "error": " / ".join(errors) or "Error al validar la universidad.",
        }, status=400)


class EspecialidadUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Permite a los administradores corregir errores de tipeo o descripción en una Especialidad.
    """
    permission_required = "directory.change_especialidad"
    model = Especialidad
    form_class = EspecialidadForm

    def form_valid(self, form):
        esp = form.save()
        messages.success(self.request, f"Especialidad '{esp.nombre}' actualizada correctamente.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_especialidades")

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar la especialidad.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_especialidades")


class UniversidadUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Permite a los administradores corregir errores de tipeo o siglas en una Universidad.
    """
    permission_required = "directory.change_universidad"
    model = Universidad
    form_class = UniversidadForm

    def form_valid(self, form):
        uni = form.save()
        messages.success(self.request, f"Universidad '{uni.nombre}' actualizada correctamente.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_universidades")

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar la universidad.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_universidades")


class EspecialidadCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Alta de especialidad desde el Dashboard administrativo.
    """
    permission_required = "directory.add_especialidad"
    model = Especialidad
    form_class = EspecialidadForm

    def form_valid(self, form):
        esp = form.save()
        messages.success(self.request, f"Especialidad '{esp.nombre}' creada exitosamente.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_especialidades")

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar la especialidad.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_especialidades")


class UniversidadCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Alta de universidad desde el Dashboard administrativo.
    """
    permission_required = "directory.add_universidad"
    model = Universidad
    form_class = UniversidadForm

    def form_valid(self, form):
        uni = form.save()
        messages.success(self.request, f"Universidad '{uni.nombre}' creada exitosamente.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_universidades")

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar la universidad.")
        return redirect(f"{reverse_lazy('accounts:dashboard')}?tab=admin_universidades")


# ==============================================================================
# VISTAS PÚBLICAS DEL DIRECTORIO (RF-07 a RF-13, CU-02, CU-03)
# ==============================================================================

class DirectorioPublicListView(ListView):
    """
    Listado público de matriculados habilitado para cualquier visitante.
    Permite buscar por nombre, apellido o matrícula y filtrar por especialidad.
    Distingue visualmente el estado de habilitación profesional.
    """
    model = Matriculado
    template_name = "directory/directorio_public_list.html"
    context_object_name = "matriculados"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Matriculado.objects.select_related("usuario")
            .prefetch_related("especialidades", "titulos__emitido_por", "estados")
            .order_by("usuario__last_name", "usuario__first_name")
        )

        query = self.request.GET.get("q", "").strip()
        especialidad_id = self.request.GET.get("especialidad", "")
        solo_activos = self.request.GET.get("solo_activos", "")

        if query:
            qs = qs.filter(
                Q(numero_matricula__icontains=query)
                | Q(usuario__first_name__icontains=query)
                | Q(usuario__last_name__icontains=query)
            )

        if especialidad_id:
            qs = qs.filter(especialidades__id=especialidad_id)

        # Distinción opcional de filtro por estado activo
        if solo_activos == "1":
            # Filtrar aquellos cuyo último estado vigente es ACTIVA
            qs = qs.filter(estados__estado=HistorialEstadoMatricula.Estado.ACTIVA).distinct()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["especialidades"] = Especialidad.objects.all().order_by("nombre")
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_especialidad"] = self.request.GET.get("especialidad", "")
        context["solo_activos"] = self.request.GET.get("solo_activos", "")
        return context


class DirectorioPublicDetailView(DetailView):
    """
    Perfil público del profesional matriculado.
    Muestra datos profesionales: matrícula, nombre, títulos, universidades, especialidades y estado.
    Respeta la Ley 25.326: correo y teléfono solo se muestran si el profesional autorizó su publicación.
    """
    model = Matriculado
    template_name = "directory/directorio_public_detail.html"
    context_object_name = "matriculado"

    def get_queryset(self):
        return (
            Matriculado.objects.select_related("usuario")
            .prefetch_related("especialidades", "titulos__emitido_por", "estados")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matriculado = self.object
        context["estado_actual"] = matriculado.estado_actual
        context["titulos"] = matriculado.titulos.select_related("emitido_por").all()
        return context

