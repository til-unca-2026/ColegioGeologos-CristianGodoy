from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('phone', 'position', 'profile_picture')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('phone', 'position', 'profile_picture')
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'position', 'is_staff')
    list_filter = ('position', 'is_staff', 'is_superuser', 'is_active')

