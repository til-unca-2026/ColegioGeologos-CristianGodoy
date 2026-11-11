from django.contrib import admin
from .models import (
    Universidad,
    Especialidad,
    Matriculado,
    Titulo,
    AntecedenteDisciplinario,
    HistorialEstadoMatricula,
)


@admin.register(Universidad)
class UniversidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sigla', 'pais')
    search_fields = ('nombre', 'sigla')
    list_filter = ('pais',)
    ordering = ('nombre',)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


class TituloInline(admin.StackedInline):
    model = Titulo
    extra = 0
    fields = (
        'denominacion',
        'tipo',
        'emitido_por',
        'fecha_egreso',
        'fecha_expedicion',
        'escaneo_diploma',
    )


class HistorialEstadoMatriculaInline(admin.TabularInline):
    model = HistorialEstadoMatricula
    extra = 0
    fields = (
        'estado',
        'fecha_desde',
        'fecha_hasta',
        'motivo',
        'origen_sancion',
        'resolucion_acta',
    )


class AntecedenteDisciplinarioInline(admin.StackedInline):
    model = AntecedenteDisciplinario
    extra = 0
    fields = (
        'numero_expediente',
        'estado_expediente',
        'tipo_sancion',
        'monto_multa',
        'fecha_inicio_sancion',
        'fecha_fin_sancion',
        'fecha_resolucion',
        'fecha_firmeza',
        'descripcion',
    )


@admin.register(Matriculado)
class MatriculadoAdmin(admin.ModelAdmin):
    inlines = [TituloInline, HistorialEstadoMatriculaInline, AntecedenteDisciplinarioInline]
    list_display = (
        'numero_matricula',
        'get_full_name',
        'get_dni',
        'fecha_matriculacion',
        'libro_folio_display',
        'get_estado_display',
        'jubilado',
    )
    list_filter = (
        'jubilado',
        'estados__estado',
        'especialidades',
        'fecha_matriculacion',
    )
    search_fields = (
        'numero_matricula',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__username',
        'usuario__dni',
        'usuario__email',
    )
    autocomplete_fields = ('usuario',)
    filter_horizontal = ('especialidades',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'creado_por', 'modificado_por')

    fieldsets = (
        ('Datos de Matrícula', {
            'fields': (
                'usuario',
                'numero_matricula',
                'fecha_matriculacion',
                ('libro', 'folio'),
                'especialidades',
                'jubilado',
            )
        }),
        ('Domicilio Profesional', {
            'fields': (
                ('domicilio_profesional_calle', 'domicilio_profesional_numero', 'domicilio_profesional_piso_depto'),
                ('domicilio_profesional_localidad', 'domicilio_profesional_provincia'),
                ('domicilio_profesional_pais', 'domicilio_profesional_cp'),
            )
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': (
                ('fecha_creacion', 'fecha_modificacion'),
                ('creado_por', 'modificado_por'),
            )
        }),
    )

    @admin.display(description='Profesional', ordering='usuario__last_name')
    def get_full_name(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username

    @admin.display(description='DNI', ordering='usuario__dni')
    def get_dni(self, obj):
        return obj.usuario.dni or "-"

    @admin.display(description='Libro / Folio')
    def libro_folio_display(self, obj):
        return f"L: {obj.libro} / F: {obj.folio}"

    @admin.display(description='Estado Actual')
    def get_estado_display(self, obj):
        estado = obj.estado_actual
        if estado:
            return estado.get_estado_display()
        return "Sin estado"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, 'creado_por') and not instance.pk and not instance.creado_por_id:
                instance.creado_por = request.user
            if hasattr(instance, 'modificado_por'):
                instance.modificado_por = request.user
            instance.save()
        formset.save_m2m()


@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    list_display = ('denominacion', 'tipo', 'matriculado', 'emitido_por', 'fecha_expedicion', 'fecha_egreso')
    list_filter = ('tipo', 'emitido_por')
    search_fields = (
        'denominacion',
        'matriculado__numero_matricula',
        'matriculado__usuario__first_name',
        'matriculado__usuario__last_name',
    )
    autocomplete_fields = ('matriculado', 'emitido_por')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'creado_por', 'modificado_por')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(AntecedenteDisciplinario)
class AntecedenteDisciplinarioAdmin(admin.ModelAdmin):
    list_display = (
        'numero_expediente',
        'matriculado',
        'tipo_sancion',
        'estado_expediente',
        'fecha_resolucion',
        'fecha_firmeza',
    )
    list_filter = ('estado_expediente', 'tipo_sancion', 'fecha_resolucion')
    search_fields = (
        'numero_expediente',
        'matriculado__numero_matricula',
        'matriculado__usuario__first_name',
        'matriculado__usuario__last_name',
        'descripcion',
    )
    autocomplete_fields = ('matriculado',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'creado_por', 'modificado_por')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistorialEstadoMatricula)
class HistorialEstadoMatriculaAdmin(admin.ModelAdmin):
    list_display = (
        'matriculado',
        'estado',
        'fecha_desde',
        'fecha_hasta',
        'motivo',
        'resolucion_acta',
    )
    list_filter = ('estado', 'fecha_desde')
    search_fields = (
        'matriculado__numero_matricula',
        'matriculado__usuario__first_name',
        'matriculado__usuario__last_name',
        'motivo',
        'resolucion_acta',
    )
    autocomplete_fields = ('matriculado', 'origen_sancion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'creado_por', 'modificado_por')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)

