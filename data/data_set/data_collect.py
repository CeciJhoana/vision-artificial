import cv2 
import os


def collect_data():
    video_path = '/home/ubu2711/Documentos/IA/vision_artificial/data/data_set/videos/canal2_20.mp4'
    save_dir = '/home/ubu2711/Documentos/IA/vision_artificial/data/data_set/images/channel_2'

     # Crear las carpetas necesarias si no existen
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

        
    captura = cv2.VideoCapture(video_path)
   
    if not captura.isOpened():
        print("No se pudo abrir el archivo de videos/canal2_20.mp4.")
        return
    
    contador =7
    while True:
        # lectura de la video captura
        lectura_fotograma, frame = captura.read()
        
        if not lectura_fotograma:
            print("No se pudo leer el fotograma. Fin del video o archivo dañado.")
            break


        cv2.imwrite(os.path.join(save_dir, f'img_channel2_{contador}.jpg'), frame)
        contador = contador + 1
        #cv2.imshow('frame', frame)
        k = cv2.waitKey(1)
        if k == 27 or contador >=10:
            break


    captura.release()
    cv2.destroyAllWindows()


collect_data()