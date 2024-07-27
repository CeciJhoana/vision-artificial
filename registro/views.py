from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.urls import reverse
from .models import Usuario, Foto
import cv2
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from .forms import RegistroForm
import math
from PIL import Image as PILImage
import mediapipe.python.solutions.face_mesh_connections as face_mesh_connections
import face_recognition as fr
import mediapipe as mp
from .models import Foto, Usuario
from .forms import RegistroForm

# Variable global para almacenar el estado de éxito
success_status = {}

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save() # Guarda el usuario en la base de datos
            request.session['usuario_id'] = user.id  # Guarda el ID del usuario en la sesión
            return redirect('video_capture')
    else:
        form = RegistroForm()

    return render(request, 'registro.html', {'form': form})

def video_capture(request):
    exito = request.GET.get('exito')
    return render(request, 'video_capture.html', {'exito': exito})

def video_feed(request):
    return StreamingHttpResponse(capture_and_save_image(request), content_type='multipart/x-mixed-replace; boundary=frame')

# Inicializa los objetos y configuraciones para la detección de rostros y la malla facial
def initialize_face_detection():
    # Heramienta de dibujo
    mpDraw = mp.solutions.drawing_utils
    ConfigDraw = mpDraw.DrawingSpec(thickness=1, circle_radius=1)
    #Objeto de la malla facial
    FacemeshObject = mp.solutions.face_mesh
    FaceMesh = FacemeshObject.FaceMesh(max_num_faces=1)
    #Objeto de detector de rostro
    FaceObject = mp.solutions.face_detection
    detector = FaceObject.FaceDetection(min_detection_confidence=0.5, model_selection=1)
    return mpDraw, ConfigDraw, FaceMesh, detector

# Procesa la imagen para detectar la malla facial y dibujar los puntos de la malla en la imagen
def process_face_mesh(frame, FaceMesh, mpDraw, ConfigDraw):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = FaceMesh.process(rgb)
    if res.multi_face_landmarks:
        # Extraer la malla de rostro
        for rostros in res.multi_face_landmarks:
            #Dibujar
            mpDraw.draw_landmarks(frame, rostros, face_mesh_connections.FACEMESH_TESSELATION, ConfigDraw, ConfigDraw)
    return res

# Obtiene las coordenadas de los puntos clave de la malla facial
def get_landmark_coordinates(res, frame):
    px, py, lista = [], [], []
    if res.multi_face_landmarks:
        for rostros in res.multi_face_landmarks:
            #Extraer puntos clave
            for id, puntos in enumerate(rostros.landmark):
                #informacion de la imagen
                alto, ancho, _ = frame.shape
                x, y = int(puntos.x * ancho), int(puntos.y * alto)
                px.append(x)
                py.append(y)
                lista.append([id, x, y])
    return px, py, lista

# Calcula las distancias entre puntos clave específicos de la malla facial
def calculate_distances(lista):
    # Ojo derecho
    x1, y1 = lista[145][1:]
    x2, y2 = lista[159][1:]
    longitud1 = math.hypot(x2 - x1, y2 - y1)
    # Ojo Izquierdo
    x3, y3 = lista[374][1:]
    x4, y4 = lista[386][1:]
    longitud2 = math.hypot(x4 - x3, y4 - y3)
    return longitud1, longitud2

# Detecta rostros en la imagen usando el detector de MediaPipe
def detect_faces(frame, detector, rgb):
    return detector.process(rgb)

# Maneja la detección de rostros, aplicando offsets y dibujando el cuadro de detección en la imagen
def handle_face_detection(faces, frame, ancho, alto, offsetx, offsety, confThreshold):
    xi = yi = an = al = xf = yf = 0
    for face in faces.detections:
        score = face.score[0]
        bbox = face.location_data.relative_bounding_box
        if score > confThreshold:
             #Convertir a pixeles los valores normalizados de bbox
            xi, yi, an, al = int(bbox.xmin * ancho), int(bbox.ymin * alto), int(bbox.width * ancho), int(bbox.height * alto)
            #Aplicar offset en x
            offsetan = int((offsetx / 100) * an)
            xi = int(xi - offsetan / 2)
            an += offsetan
            xf = xi + an
            #Aplicar offset en y
            offsetal = int((offsety / 100) * al)
            yi = int(yi - offsetal)
            al += offsetal
            yf = yi + al
            cv2.rectangle(frame, (xi, yi, an, al), (255, 0, 255), 2)
    return xi, yi, an, al, xf, yf


def capture_and_save_image(request):
    # Usa la cámara del dispositivo
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return JsonResponse({'error': 'No se puede abrir la cámara.'})

    parpadeo = False
    conteo = 0
    # Offset
    offsety = 40
    offsetx = 20
    #tumbral de presición
    confThreshold = 0.5
    mpDraw, ConfigDraw, FaceMesh, detector = initialize_face_detection()
    
    # Obtener el usuario que se está registrando
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        camera.release()
        return JsonResponse({'redirect_url': reverse('registro')})

    usuario = Usuario.objects.get(id=usuario_id)

    while True:
        success, frame = camera.read()
        if not success or frame is None:
            print("Error al capturar el frame de la cámara.")
            continue

        frameSave = frame.copy()

        res = process_face_mesh(frame, FaceMesh, mpDraw, ConfigDraw)
        #lista de resuktados
        px, py, lista = get_landmark_coordinates(res, frame)

        if len(lista) == 468:
            longitud1, longitud2 = calculate_distances(lista)
            faces = detect_faces(frame, detector, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if faces.detections is not None:
                xi, yi, an, al, xf, yf = handle_face_detection(faces, frame, frame.shape[1], frame.shape[0], offsetx, offsety, confThreshold)
                x7, y7 = lista[70][1:]
                x8, y8 = lista[300][1:]

                # Caso en el que el rostro mira al frente
                if x7 > lista[139][1] and x8 < lista[368][1]:
                    # Contador de Parpadeos
                    if longitud1 <= 10 and longitud2 <= 10 and not parpadeo:
                        conteo += 1
                        parpadeo = True
                    elif longitud1 > 10 and longitud2 > 10 and parpadeo:
                        parpadeo = False
                    
                    # Condicion si parpadea 3 o hasta mayor a tres
                    if conteo >= 3:

                        cv2.rectangle(frame, (xi, yi, an, al), (0, 255, 0), 2)
                        # condicion para sacar foto con los ojos abiertos
                        if longitud1 > 15 and longitud2 > 15:
                            if yi < 0: yi = 0
                            if xi < 0: xi = 0
                            if yf > frameSave.shape[0]: yf = frameSave.shape[0]
                            if xf > frameSave.shape[1]: xf = frameSave.shape[1]
                            # Vamos a cortar las pixeles
                            # Almacenar el rotro en la base de datos segun al usuario y los datos que se puso en registro
                            cut = frameSave[yi:yf, xi:xf]
                            if cut.size > 0: # Verificar que la imagen no está vacía
                                image_pil = PILImage.fromarray(cv2.cvtColor(cut, cv2.COLOR_BGR2RGB))
                                image_io = BytesIO()
                                image_pil.save(image_io, format='JPEG')
                                image_file = ContentFile(image_io.getvalue(), 'rostro.jpg')
                                # Almacenar la imagen en la base de datos
                                Foto.objects.create(usuario=usuario, imagen=image_file)
                                # Actualizar el estado de éxito
                                success_status[usuario_id] = True  
                                break
                            else:
                                print("Error: La imagen recortada está vacía.")
                else:
                    conteo = 0
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    camera.release() # Libera el recurso de la cámara   
    cv2.destroyAllWindows()

#verifica si la imagen se ha guardado correctamente.
def check_success(request):
    
    usuario_id = request.session.get('usuario_id')
    if usuario_id and success_status.get(usuario_id):
        return JsonResponse({'exito': True})
    return JsonResponse({'exito': False})
