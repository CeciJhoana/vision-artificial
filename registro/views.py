from django.shortcuts import render, redirect
from .forms import RegistroForm
from .models import Usuario
from django.http import StreamingHttpResponse
import cv2


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

def video_capture(request):
    return render(request, 'video_capture.html')

def gen_frames():
    camera = cv2.VideoCapture(0)  # Usa la cámara del dispositivo
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')