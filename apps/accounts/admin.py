from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MembresiaComision, User


class MembresiaComisionInline(admin.TabularInline):
    model = MembresiaComision
    fk_name = "usuario"
    extra = 0
    fields = ('comision', 'cargo', 'fecha_desde', 'fecha_hasta', 'creado_por')
    readonly_fields = ('creado_por',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(MembresiaComision)
class MembresiaComisionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'comision', 'cargo', 'fecha_desde', 'fecha_hasta', 'vigente_status')
    list_filter = ('comision', 'cargo', 'fecha_desde')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'usuario__dni')
    date_hierarchy = 'fecha_desde'

    @admin.display(description='Estado', boolean=True)
    def vigente_status(self, obj):
        return obj.es_vigente

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [MembresiaComisionInline]
    fieldsets = UserAdmin.fieldsets + (
        ('Identificación (Ley 25.326)', {
            'fields': (
                'dni',
                'cuil_cuit',
                'fecha_nacimiento',
                'lugar_nacimiento',
                'nacionalidad',
            )
        }),
        ('Contacto y Publicación', {
            'fields': (
                'phone',
                'publicar_email',
                'publicar_telefono',
                'profile_picture',
            )
        }),
        ('Domicilio Real (Ley 25.326)', {
            'fields': (
                'domicilio_real_calle',
                'domicilio_real_numero',
                'domicilio_real_piso_depto',
                'domicilio_real_localidad',
                'domicilio_real_provincia',
                'domicilio_real_pais',
                'domicilio_real_cp',
            )
        }),
        ('Seguridad y Auditoría', {
            'fields': (
                'must_change_password',
                'creado_por',
                'modificado_por',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'usable_password', 'password1', 'password2'),
        }),
        ('Identificación Oficial (Ley 25.326)', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'dni',
                'cuil_cuit',
                'fecha_nacimiento',
                'lugar_nacimiento',
                'nacionalidad',
            ),
        }),
        ('Contacto y Publicación', {
            'fields': (
                'phone',
                'publicar_email',
                'publicar_telefono',
                'profile_picture',
            ),
        }),
        ('Domicilio Real (Ley 25.326)', {
            'fields': (
                'domicilio_real_calle',
                'domicilio_real_numero',
                'domicilio_real_piso_depto',
                'domicilio_real_localidad',
                'domicilio_real_provincia',
                'domicilio_real_pais',
                'domicilio_real_cp',
            ),
        }),
        ('Seguridad y Acceso', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'must_change_password',
            ),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'dni', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'must_change_password')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'dni', 'cuil_cuit')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
            if not obj.must_change_password:
                obj.must_change_password = True
        else:
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)

