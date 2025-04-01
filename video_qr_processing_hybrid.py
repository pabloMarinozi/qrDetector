import cv2
import sys
import os
import shutil
import numpy as np
import multiprocessing
from pyzbar.pyzbar import decode
from utils import mide_tiempo


def es_rectangulo_valido(points):
    """
    Verifica si los puntos forman un cuadrilátero válido basado en si los lados opuestos son paralelos.

    Args:
        points (list): Lista de puntos con coordenadas (x, y).

    Returns:
        bool: True si los puntos forman un cuadrilátero válido, False en caso contrario.
    """
    # Convertir puntos a un arreglo numpy
    pts = np.array(points, np.int32)

    # Calcular los vectores de los lados
    def calcular_vector(p1, p2):
        return np.array([p2[0] - p1[0], p2[1] - p1[1]])
      
    v1 = calcular_vector(pts[0], pts[1])  # Lado 1
    v2 = calcular_vector(pts[1], pts[2])  # Lado 2
    v3 = calcular_vector(pts[3], pts[2])  # Lado 3
    v4 = calcular_vector(pts[0], pts[3])  # Lado 4

    # Calcular los ángulos entre lados opuestos
    def calcular_angulo_entre_vectores(v1, v2):
        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angulo = np.arccos(np.clip(cos_theta, -1.0, 1.0))
        return np.degrees(angulo)

    angulo_opuesto1 = calcular_angulo_entre_vectores(v1, v3)
    angulo_opuesto2 = calcular_angulo_entre_vectores(v2, v4)

    # Comprobar si los ángulos entre lados opuestos son cercanos a 0 grados (con un umbral)
    umbral = 10  # Grados de tolerancia para considerar que son paralelos
    if abs(angulo_opuesto1) > umbral or abs(angulo_opuesto2) > umbral:
        return False

    # Si todas las validaciones pasan, devolver True
    return True


def procesar_frame_range(video_path: str, log_path: str, start_frame: int, end_frame: int, output:str, borde: int = 15, tamano_parche: int = 300):
    """
    Procesa un rango de frames de un video para detectar códigos QR de manera híbrida:
    1. Usa pyzbar para detectar códigos QR dividiendo la imagen en parches más pequeños.
    2. Recorta el área del QR detectado con un borde adicional para mejorar la detección.
    3. Usa OpenCV para encontrar las esquinas exactas del QR en el área recortada.

    Args:
        video_path (str): Ruta al archivo de video.
        log_path (str): Ruta al archivo de log para registrar errores.
        start_frame (int): Frame inicial para comenzar el procesamiento.
        end_frame (int): Frame final hasta donde se debe procesar.
        borde (int): Tamaño del borde adicional para el recorte del área del QR (valor por defecto 15).
        tamano_parche (int): Tamaño del parche en el cual se dividirá cada frame (valor por defecto 200).

    Returns:
        list: Lista de diccionarios con información sobre los códigos QR detectados.
    """
    datos = []
    os.makedirs(f'{output}/qr_frames/', exist_ok=True)
    cap = cv2.VideoCapture(video_path)    
    frame_num = 0

    while frame_num < end_frame and cap.isOpened():

        ret, frame = cap.read()

        if frame_num < start_frame:
            frame_num += 1
            continue
            
        if not ret:
            if not ret:
                print(f"Error al leer el frame {frame_num}.")
                frame_num += 1
                continue
          
        try:
            # Dividir el frame en parches más pequeños
            height, width, _ = frame.shape
            for y in range(0, height, tamano_parche):
                for x in range(0, width, tamano_parche):
                    # Definir los límites del parche
                    x_end = min(x + tamano_parche, width)
                    y_end = min(y + tamano_parche, height)

                    # Extraer el parche
                    parche = frame[y:y_end, x:x_end]

                    # Detectar los códigos QR utilizando pyzbar en el parche
                    qrs = decode(parche)

                    for qr in qrs:
                        # Bounding box del QR (esquina superior izquierda y dimensiones)
                        (px, py, pw, ph) = qr.rect

                        # Expandir el área del QR para mejorar la detección de esquinas, con un borde adicional de 'borde' píxeles
                        x_start = max(0, x + px - borde)
                        y_start = max(0, y + py - borde)
                        x_final = min(width, x + px + pw + borde)
                        y_final = min(height, y + py + ph + borde)

                        # Recortar la región del QR
                        qr_region = frame[y_start:y_final, x_start:x_final].copy()

                        # Guardar la región en disco para verificación
                        data = qr.data.decode('utf-8')

                        # Usar OpenCV para encontrar las esquinas exactas del QR en la región recortada
                        qr_detector = cv2.QRCodeDetector()
                        retval, points = qr_detector.detect(qr_region)

                        if retval and points is not None:
                            # Dibujar los puntos detectados por OpenCV antes de la conversión a coordenadas globales
                            points = points[0]  # points tiene una dimensión adicional que contiene los puntos

                            # Validar si los puntos forman un rectángulo válido
                            if es_rectangulo_valido(points):
                                # Convertir los puntos a coordenadas relativas a la imagen completa
                                puntos_qr = [(int(point[0]) + x_start, int(point[1]) + y_start) for point in points]

                                # Dibujar los puntos en el frame completo
                                for punto in puntos_qr:
                                    cv2.circle(frame, punto, radius=5, color=(0, 0, 255), thickness=-1)  # Rojo para los puntos detectados
                                cv2.putText(frame, data, (puntos_qr[0][0] - 10, puntos_qr[0][1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

                                # Añadir la información del QR detectado con OpenCV
                                datos.append({
                                    'frame': frame_num,
                                    'data': data,
                                    'x1': puntos_qr[0][0], 'y1': puntos_qr[0][1],
                                    'x2': puntos_qr[1][0], 'y2': puntos_qr[1][1],
                                    'x3': puntos_qr[2][0], 'y3': puntos_qr[2][1],
                                    'x4': puntos_qr[3][0], 'y4': puntos_qr[3][1],
                                    'detected_by': 'opencv'
                                })

        except Exception as e:
            # Registrar cualquier error en el archivo de log
            with open(log_path, 'a') as log_file:
                log_file.write(f'Error en el frame {frame_num}: {str(e)}\n')

        # Guardar el frame completo con los puntos dibujados si ha sido modificado
        cv2.imwrite(f'{output}/qr_frames/frame_completo_{frame_num}.png', frame)

        frame_num += 1

    cap.release()
    return datos

@mide_tiempo
def procesar_video_parallel(video_path: str, log_path: str, output_path: str, num_processes: int = 4, borde: int = 15):
    """
    Procesa un video en paralelo utilizando múltiples procesos para detectar códigos QR de manera híbrida.

    Args:
        video_path (str): Ruta al archivo de video.
        log_path (str): Ruta al archivo de log para registrar errores.
        num_processes (int): Número de procesos a utilizar para la ejecución paralela.
        borde (int): Tamaño del borde adicional para el recorte del área del QR (valor por defecto 15).

    Returns:
        list: Lista de diccionarios con información sobre los códigos QR detectados.
    """
    # Borrar la carpeta 'regiones' si existe y crearla de nuevo
    if os.path.exists('regiones'):
        shutil.rmtree('regiones')
    os.makedirs('regiones')

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    frame_ranges = [(i * (total_frames // num_processes), (i + 1) * (total_frames // num_processes)) for i in range(num_processes)]    
    frame_ranges[-1] = (frame_ranges[-1][0], total_frames)  # Asegurarse de que el último proceso llegue hasta el final

    # # Imprimir los rangos generados
    # print("Rangos de frames asignados a los procesos:")
    # for i, (start, end) in enumerate(frame_ranges):
    #     print(f"Proceso {i}: Frames {start} a {end - 1}")

    # Mostrar mensaje inicial
    print(f"Procesando video con {num_processes} núcleos...")

    # Crear procesos y recolectar resultados
    pool = multiprocessing.Pool(processes=num_processes)
    results = pool.starmap(procesar_frame_range, [(video_path, log_path, start, end, output_path, borde) for start, end in frame_ranges])

    pool.close()
    pool.join()

    # Unir los resultados de todos los procesos
    datos = [item for sublist in results for item in sublist]
    return datos
