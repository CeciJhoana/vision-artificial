import math
from django.shortcuts import render, redirect
from .forms import RegistroForm
from .models import Usuario
from django.http import StreamingHttpResponse
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
    parpadeo=False
    conteo = 0
    muestra = 0
    step = 0

    # Offset
    offsety=40
    offsetx=20
    #tumbral de presición
    confThreshold =0.5
    # Heramienta de dibujo
    mpDraw = mp.solutions.drawing_utils
    ConfigDraw = mpDraw.DrawingSpec(thickness = 1, circle_radius = 1)
    #Objeto de la malla facial
    FacemeshObject = mp.solutions.face_mesh
    FaceMesh = FacemeshObject.FaceMesh(max_num_faces=1)
    #Objeto de detector de rostro
    FaceObject = mp.solutions.face_detection
    detector = FaceObject.FaceDetection(min_detection_confidence=0.5, model_selection=1)
    while True:
        success, frame = camera.read()
        frameSave = frame.copy()
        if not success:
            break
        else:
            rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            res = FaceMesh.process(rgb)
            

            #lista de resuktados
            px=[]
            py=[]
            lista=[]


            if res.multi_face_landmarks:
                # Extraer la malla de rostro
                for rostros in res.multi_face_landmarks:

                    #Dibujar
                    mpDraw.draw_landmarks(frame, rostros, face_mesh_connections.FACEMESH_TESSELATION, ConfigDraw, ConfigDraw)

                    #Extraer puntos clave
                    for id, puntos in enumerate(rostros.landmark):

                        # Informacion de la imagen
                        alto, ancho, c = frame.shape
                        x, y = int(puntos.x * ancho), int(puntos.y * alto)
                        px.append(x)
                        py.append(y)
                        lista.append([id, x, y])
                        # hay 468 puntos
                          # Ojo derecho
                        if len(lista) == 468:
                            # Ojo derecho
                            x1, y1 = lista[145][1:]
                            x2, y2 = lista[159][1:]
                            
                            longitud1 = math.hypot(x2 - x1, y2 - y1)
                            #print(longitud1)

                            # Ojo Izquierdo
                            x3, y3 = lista[374][1:]
                            x4, y4 = lista[386][1:]
                            
                            longitud2 = math.hypot(x4 - x3, y4 - y3)
                            #print(longitud2)

                            # Parietal Derecho
                            x5, y5 = lista[139][1:]
                            # Parietal Izquierdo
                            x6, y6 = lista[368][1:]

                            # Ceja Derecha
                            x7, y7 = lista[70][1:]
                            # Ceja Izquierda
                            x8, y8 = lista[300][1:]

                            # Detector de rostro
                            faces = detector.process(rgb)

                            if faces.detections is not None:
                                for face in faces.detections:

                                    score = face.score
                                    score = score[0] 
                                    bbox = face.location_data.relative_bounding_box
                                     # Threshold
                                    if score > confThreshold:
                                       #Convertir a pixeles los valores normalizados de bbox
                                        xi, yi, an, al = bbox.xmin, bbox.ymin, bbox.width, bbox.height
                                        xi, yi, an, al = int(xi * ancho), int(yi * alto), int(
                                            an * ancho), int(al * alto)
                                        #Aplicar offset en x
                                        offsetan= (offsetx / 100)* an
                                        xi = int(xi-int(offsetan/2))
                                        an = int(an + offsetan)
                                        xf = xi + an
                                        #Aplicar offset en y
                                        offsetal = (offsety / 100) * al
                                        yi = int(yi - offsetal)
                                        al = int(al + offsetal)
                                        yf = yi + al

                                        # Pasos de verificacion
                                        if step == 0:
                                            # dibujar el recuadro
                                            cv2.rectangle(frame,(xi,yi,an,al), (255,0,255),2)

                                    # Caso en el que el rostro mira al frente
                                    if x7 > x5 and x8 < x6:
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
                                                    # Vamos a cortar las pixeles
                                                    cut = frameSave[yi:yf, xi:xf] 
                                                    # Almacenar el rotro en la base de datos segun al usuario y los datos que se puso en registro

                                                    #Pasar siguiente paso 
                                                    step = 1
                                            
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
            
        



def video_feed(request):
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

