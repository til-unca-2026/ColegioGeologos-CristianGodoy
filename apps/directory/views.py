from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, TemplateView, View
from apps.documents.models import Documento
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

        # El título es opcional. Si se cargó denominación o universidad, se valida; si vino vacío, es válido no guardar título.
        tiene_datos_titulo = any([
            request.POST.get("titulo-denominacion"),
            request.POST.get("titulo-emitido_por"),
            request.POST.get("titulo-fecha_egreso"),
            request.POST.get("titulo-fecha_expedicion"),
            request.FILES.get("titulo-escaneo_diploma"),
        ])

        if tiene_datos_titulo:
            # Si se intentó cargar título, requerimos denominación, universidad emisora y nivel/tipo
            if not request.POST.get("titulo-denominacion"):
                titulo_form.add_error("denominacion", "Si carga un título, debe especificar la denominación.")
            if not request.POST.get("titulo-emitido_por"):
                titulo_form.add_error("emitido_por", "Si carga un título, debe indicar la universidad emisora.")
            if not request.POST.get("titulo-tipo"):
                titulo_form.add_error("tipo", "Si carga un título, debe indicar el nivel.")

        titulo_valido = not tiene_datos_titulo or titulo_form.is_valid()

        if form.is_valid() and titulo_valido:
            return self.form_valid(form, titulo_form if tiene_datos_titulo else None)
        else:
            return self.form_invalid(form, titulo_form)

    def form_valid(self, form, titulo_form=None):
        with transaction.atomic():
            matriculado = form.save(commit=False)
            matriculado.creado_por = self.request.user
            matriculado.save()
            form.save_m2m()

            # Guardar el título universitario vinculado al nuevo matriculado si fue provisto
            titulo = None
            if titulo_form:
                titulo = titulo_form.save(commit=False)
                titulo.matriculado = matriculado
                titulo.creado_por = self.request.user
                titulo.save()

            # Generar estado inicial ACTIVA automáticamente
            from django.utils import timezone
            fecha_inicio = matriculado.fecha_matriculacion or timezone.localdate()
            folio_txt = matriculado.folio if matriculado.folio is not None else '-'
            libro_txt = matriculado.libro or '-'
            HistorialEstadoMatricula.objects.create(
                matriculado=matriculado,
                estado=HistorialEstadoMatricula.Estado.ACTIVA,
                fecha_desde=fecha_inicio,
                motivo="Alta inicial en el padrón de matriculados",
                resolucion_acta=f"Libro {libro_txt} Folio {folio_txt}",
                creado_por=self.request.user,
            )

            # Asignar automáticamente el grupo 'matriculados' al usuario
            from django.contrib.auth.models import Group
            grupo_matriculados = Group.objects.filter(name__iexact="matriculados").first()
            if grupo_matriculados:
                matriculado.usuario.groups.add(grupo_matriculados)

        if titulo:
            msg = f"Matrícula N° {matriculado.numero_matricula} y título '{titulo.denominacion}' registrados exitosamente."
        else:
            msg = f"Matrícula N° {matriculado.numero_matricula} registrada exitosamente."
        messages.success(self.request, msg)
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
        context["antecedentes"] = matriculado.antecedentes.all().order_by("-fecha_firmeza")
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
    template_name = "directory/titulo_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["denominacion"].required = True
        form.fields["tipo"].required = True
        form.fields["emitido_por"].required = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        context["matriculado"] = matriculado
        context["title"] = "Agregar Título Universitario"
        return context

    def form_valid(self, form):
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        titulo = form.save(commit=False)
        titulo.matriculado = matriculado
        titulo.creado_por = self.request.user
        titulo.save()
        messages.success(self.request, f"Título '{titulo.denominacion}' agregado con éxito.")
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("directory:matriculado_detail", pk=matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el título. Por favor revise los campos.")
        return super().form_invalid(form)


class TituloUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Edita un título existente de un matriculado para subsanar errores de tipeo o fechas.
    """
    permission_required = "directory.change_titulo"
    model = Titulo
    form_class = TituloForm
    template_name = "directory/titulo_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["denominacion"].required = True
        form.fields["tipo"].required = True
        form.fields["emitido_por"].required = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matriculado"] = self.object.matriculado
        context["title"] = f"Editar Título: {self.object.denominacion}"
        return context

    def form_valid(self, form):
        titulo = form.save(commit=False)
        titulo.modificado_por = self.request.user
        titulo.save()
        messages.success(self.request, f"Título '{titulo.denominacion}' actualizado correctamente.")
        return redirect("directory:matriculado_detail", pk=titulo.matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el título. Por favor revise los campos.")
        return super().form_invalid(form)


class HistorialEstadoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Registra un cambio de estado en la matrícula (ej. SUSPENDIDA, ACTIVA, BAJA).
    """
    permission_required = "directory.add_historialestadomatricula"
    model = HistorialEstadoMatricula
    form_class = HistorialEstadoMatriculaForm
    template_name = "directory/historialestadomatricula_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        context["matriculado"] = matriculado
        context["title"] = "Registrar Cambio de Estado"
        return context

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
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("directory:matriculado_detail", pk=matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el cambio de estado. Por favor revise las fechas y campos.")
        return super().form_invalid(form)


class HistorialEstadoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Edita un registro del historial de estado para subsanar errores de tipeo, fechas o actas.
    """
    permission_required = "directory.change_historialestadomatricula"
    model = HistorialEstadoMatricula
    form_class = HistorialEstadoMatriculaForm
    template_name = "directory/historialestadomatricula_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matriculado"] = self.object.matriculado
        context["title"] = f"Editar Estado: {self.object.get_estado_display()}"
        return context

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
        return super().form_invalid(form)


class AntecedenteDisciplinarioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Registra un antecedente disciplinario o sanción contra un matriculado.
    """
    permission_required = "directory.add_antecedentedisciplinario"
    model = AntecedenteDisciplinario
    form_class = AntecedenteDisciplinarioForm
    template_name = "directory/antecedentedisciplinario_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matriculado = get_object_or_404(Matriculado, pk=self.kwargs["matriculado_id"])
        context["matriculado"] = matriculado
        context["title"] = "Registrar Antecedente Disciplinario"
        return context

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
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("directory:matriculado_detail", pk=matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el antecedente disciplinario.")
        return super().form_invalid(form)


class AntecedenteDisciplinarioUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Edita un antecedente disciplinario para subsanar errores de tipeo, montos o expedientes.
    """
    permission_required = "directory.change_antecedentedisciplinario"
    model = AntecedenteDisciplinario
    form_class = AntecedenteDisciplinarioForm
    template_name = "directory/antecedentedisciplinario_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matriculado"] = self.object.matriculado
        context["title"] = f"Editar Antecedente Exp. {self.object.numero_expediente}"
        return context

    def form_valid(self, form):
        antecedente = form.save(commit=False)
        antecedente.modificado_por = self.request.user
        antecedente.save()
        messages.success(self.request, f"Antecedente Exp. {antecedente.numero_expediente} actualizado correctamente.")
        return redirect("directory:matriculado_detail", pk=antecedente.matriculado.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el antecedente disciplinario.")
        return super().form_invalid(form)


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

class MatriculacionTramitesView(TemplateView):
    """
    Vista pública informativa sobre requisitos de matriculación, renovación y trámites (RF-05, RF-06).
    Muestra la guía del circuito administrativo y modelos de notas/formularios oficiales disponibles.
    """
    template_name = "directory/matriculacion_tramites.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        doc_qs = Documento.objects.filter(
            vigente=True,
            categoria=Documento.Categoria.MODELO
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

        context["modelos_notas"] = doc_qs.order_by("-fecha_documento", "-fecha_creacion")
        return context


class DirectorioPublicListView(ListView):
    """
    Listado público de matriculados habilitado para cualquier visitante (RF-07, RF-08, RF-09).
    Permite buscar por nombre, apellido o matrícula y filtrar por especialidad.
    Refleja fidedignamente el padrón con todos los estados de matrícula (activa, suspendida, baja)
    y distingue visualmente a los habilitados al día para garantizar la fe pública registral.
    """
    model = Matriculado
    template_name = "directory/directorio_public_list.html"
    context_object_name = "matriculados"
    paginate_by = 12

    def get_queryset(self):
        from django.db.models.functions import Cast
        from django.db.models import IntegerField

        qs = (
            Matriculado.objects.select_related("usuario")
            .prefetch_related("especialidades", "titulos__emitido_por", "estados")
            .annotate(
                # Si el número de matrícula es numérico lo ordena como entero, si no mantiene el orden texto descendente
                num_mat_int=Cast("numero_matricula", output_field=IntegerField())
            )
            .order_by("-num_mat_int", "-numero_matricula")
        )

        query = self.request.GET.get("q", "").strip()
        especialidad_id = self.request.GET.get("especialidad", "")

        if query:
            qs = qs.filter(
                Q(numero_matricula__icontains=query)
                | Q(usuario__first_name__icontains=query)
                | Q(usuario__last_name__icontains=query)
            )

        if especialidad_id:
            qs = qs.filter(especialidades__id=especialidad_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["especialidades"] = Especialidad.objects.all().order_by("nombre")
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_especialidad"] = self.request.GET.get("especialidad", "")
        return context


class DirectorioPublicDetailView(DetailView):
    """
    Perfil público del profesional matriculado (RF-10, RF-11, RF-12, RF-13).
    Muestra datos profesionales: matrícula, nombre, títulos, universidades, especialidades y estado registral real.
    Respeta la Ley 25.326: correo y teléfono solo se muestran si el profesional autorizó voluntariamente su publicación.
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

