from django.contrib import admin
from .models import Usuario, Foto
# Register your models here.

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'nombre_usuario', 'edad', 'email')
    search_fields = ('nombre', 'apellido', 'nombre_usuario', 'email')

class FotoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'imagen', 'fecha_subida')
    search_fields = ('usuario__nombre_usuario',)
    list_filter = ('fecha_subida',)

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Foto, FotoAdmin)

