import math
from django.http import HttpResponse
from urllib import request
from django.shortcuts import render, redirect
from .forms import RegistroForm
from .models import Foto, Usuario
from django.http import StreamingHttpResponse
from django.core.files.base import ContentFile
from PIL import Image as PILImage
from io import BytesIO
import mediapipe.python.solutions.face_mesh_connections as face_mesh_connections
#-------Librerias------ 
import cv2
import face_recognition as fr
import mediapipe as mp

# Create your views here.

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el usuario en la base de datos
            request.session['usuario_id'] = user.id  # Guarda el ID del usuario en la sesión
            return redirect('video_capture')
    else:
        form = RegistroForm()

    return render(request, 'registro.html', {'form': form})

def success_page(request):
    #return HttpResponse("Registro guardado con éxito")
    return render(request, 'success.html')




def video_capture(request):
    return render(request, 'video_capture.html')

# Inicializa los objetos y configuraciones para la detección de rostros y la malla facial
def initialize_face_detection():
   # Heramienta de dibujo
    mpDraw = mp.solutions.drawing_utils
    ConfigDraw = mpDraw.DrawingSpec(thickness = 1, circle_radius = 1)
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

def gen_frames(request):
    camera = cv2.VideoCapture(0)  # Usa la cámara del dispositivo
    parpadeo=False
    conteo = 0
    step = 0
    # Offset
    offsety=40
    offsetx=20
    #tumbral de presición
    confThreshold =0.5
    mpDraw, ConfigDraw, FaceMesh, detector = initialize_face_detection()
   
    # Obtener el usuario que se está registrando
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return

    usuario = Usuario.objects.get(id=usuario_id)

    while True:
        success, frame = camera.read()
        frameSave = frame.copy()
        if not success:
            break
        else:
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
                            #Poner un check en la interfaz indicando que si esta mirando al frende
                            # Contador de Parpadeos
                            #Ajustar el umbral qu este caso se puso 10
                            if longitud1 <= 10 and longitud2 <= 10 and parpadeo == False:  # Parpadeo
                                conteo = conteo + 1
                                parpadeo = True

                            elif longitud1 > 10 and longitud2 > 10 and parpadeo == True:  # Seguridad parpadeo
                                parpadeo = False

                                            
                                # Parpadeos
                                # Conteo de parpadeos que se muestre en pantalla 
                                # Condicion si parpadea 3 o hasta mayor a tres
                            if conteo >= 3:
                                # Mostrar en pantalla el check de que se parpadeo los correctos

                                # condicion para sacar foto con los ojos abiertos
                                if longitud1 > 15 and longitud2 > 15: 
                                    if yi < 0: yi = 0
                                    if xi < 0: xi = 0
                                    if yf > frameSave.shape[0]: yf = frameSave.shape[0]
                                    if xf > frameSave.shape[1]: xf = frameSave.shape[1]
                                    # Vamos a cortar las pixeles
                                    cut = frameSave[yi:yf, xi:xf] 
                                    # Almacenar el rotro en la base de datos segun al usuario y los datos que se puso en registro
                                    if cut.size > 0:  # Verificar que la imagen no está vacía
                                        # Convertir la imagen en formato compatible con Django usando Pillow
                                        image_pil = PILImage.fromarray(cv2.cvtColor(cut, cv2.COLOR_BGR2RGB))
                                        image_io = BytesIO()
                                        image_pil.save(image_io, format='JPEG')
                                        image_file = ContentFile(image_io.getvalue(), 'rostro.jpg')
                                        cv2.rectangle(frame,(xi,yi,an,al), (0,255,0),2)
                                        # Almacenar la imagen en la base de datos
                                        Foto.objects.create(usuario=usuario, imagen=image_file)
                                        step = 1
                                        
                                        # Romper el ciclo while para detener la captura de video
                                       # camera.release()
                                        #cv2.destroyAllWindows()
                                        
                                       # return HttpResponse("DONE")
                                       
                                       # return redirect('success')
                                        break
                                    else:
                                        print("Error: La imagen recortada está vacía.")
                                                
                        else : conteo = 0

                        if step ==1: 
                            # dibujar el recuadro
                            cv2.rectangle(frame,(xi,yi,an,al), (0,255,0),2)

                            # Poner en pantlla el check liveness 
                            # Asegurando asi que se hizo correctamente                               

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    camera.release()  # Libera el recurso de la cámara    
    cv2.destroyAllWindows()
    return render(request, 'success.html')
    #yield (b'--frame\r\n'
     #      b'Content-Type: text/plain\r\n\r\n' + b'DONE' + b'\r\n')
        





def video_feed(request):
    return StreamingHttpResponse(gen_frames(request), content_type='multipart/x-mixed-replace; boundary=frame')

