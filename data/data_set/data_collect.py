import cv2 
import os


def collect_data():
    video_path = '/home/ubu2711/Documentos/IA/vision_artificial/data/data_set/videos/channel_15/isa_ch15_main_20240710140800_20240710140830.mp4'
    save_dir = '/home/ubu2711/Documentos/IA/vision_artificial/data/data_set/images'

     # Crear las carpetas necesarias si no existen
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

        
    captura = cv2.VideoCapture(video_path)
   
    if not captura.isOpened():
        print("No se pudo abrir el archivo de videos/canal2_20.mp4.")
        return
    
    fps = captura.get(cv2.CAP_PROP_FPS)  # Obtener la tasa de fotogramas del video
    intervalo_frames = int(fps * 2)  # Número de fotogramas correspondientes a 2 segundos

    contador =55
    frame_id = 0
    while True:
        # lectura de la video captura
        lectura_fotograma, frame = captura.read()
        
        if not lectura_fotograma:
            print("No se pudo leer el fotograma. Fin del video o archivo dañado.")
            break

        if frame_id % intervalo_frames == 0:  # Capturar una imagen cada 2 segundos
            cv2.imwrite(os.path.join(save_dir, f'img_ch15_{contador}.jpg'), frame)
           
            contador += 1
        
        frame_id += 1
      
        k = cv2.waitKey(1)
        if k == 27 or contador >=95:
            break


    captura.release()
    cv2.destroyAllWindows()


collect_data()