from django.db import models

# Create your models here.

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    nombre_usuario = models.CharField(max_length=100, unique=True)
    edad = models.IntegerField()
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nombre_usuario
    
class Foto(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='fotos/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.usuario.nombre_usuario}"