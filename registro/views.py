from django.shortcuts import render, redirect
from .forms import RegistroForm
from .models import Usuario

# Create your views here.

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()  # Guarda el usuario en la base de datos
            return redirect('success')
    else:
        form = RegistroForm()

    return render(request, 'registro.html', {'form': form})

def success(request):
    return render(request, 'success.html')