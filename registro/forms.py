
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .models import Usuario

class RegistroForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'nombre_usuario', 'edad', 'email']

    def clean_nombre_usuario(self):
        nombre_usuario = self.cleaned_data['nombre_usuario']
        if Usuario.objects.filter(nombre_usuario=nombre_usuario).exists():
            raise ValidationError("El nombre de usuario ya existe")
        return nombre_usuario

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith('@gmail.com'):
            raise ValidationError("Solo se aceptan correos de Gmail")
        return email
