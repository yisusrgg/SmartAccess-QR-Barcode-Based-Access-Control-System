from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'estado', 'fecha_registro')
    search_fields = ('username', 'email')
    list_filter = ('estado', 'fecha_registro')
