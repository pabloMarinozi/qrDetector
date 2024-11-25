import cv2
import sys
import multiprocessing
from pyzbar.pyzbar import decode


def procesar_frame_range(video_path: str, log_path: str, start_frame: int, end_frame: int):
    """
    Procesa un rango de frames de un video para detectar códigos QR con mayor precisión.

    Args:
        video_path (str): Ruta al archivo de video.
        log_path (str): Ruta al archivo de log para registrar errores.
        start_frame (int): Frame inicial para comenzar el procesamiento.
        end_frame (int): Frame final hasta donde se debe procesar.

    Returns:
        list: Lista de diccionarios con información sobre los códigos QR detectados.
    """
    datos = []
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frame_num = start_frame

    while frame_num < end_frame and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        try:
            # Detectar los códigos QR utilizando pyzbar
            qrs = decode(frame)

            for qr in qrs:
                # Obtener las esquinas del polígono del QR
                polygon = qr.polygon
                if len(polygon) == 4:  # Asegurarse de que sea un cuadrilátero
                    points = [(point.x, point.y) for point in polygon]
                else:
                    continue  # Saltar si no es un cuadrilátero

                # Obtener los datos del QR
                data = qr.data.decode('utf-8')

                # Añadir la información del QR detectado
                datos.append({
                    'frame': frame_num,
                    'data': data,
                    'points': points  # Las cuatro esquinas del QR
                })

        except Exception as e:
            # Registrar cualquier error en el archivo de log
            with open(log_path, 'a') as log_file:
                log_file.write(f'Error en el frame {frame_num}: {str(e)}\n')

        frame_num += 1

    cap.release()
    return datos


def procesar_video_parallel(video_path: str, log_path: str, num_processes: int = 4):
    """
    Procesa un video en paralelo utilizando múltiples procesos para detectar códigos QR.

    Args:
        video_path (str): Ruta al archivo de video.
        log_path (str): Ruta al archivo de log para registrar errores.
        num_processes (int): Número de procesos a utilizar para la ejecución paralela.

    Returns:
        list: Lista de diccionarios con información sobre los códigos QR detectados.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    frame_ranges = [(i * (total_frames // num_processes), (i + 1) * (total_frames // num_processes)) for i in range(num_processes)]
    frame_ranges[-1] = (frame_ranges[-1][0], total_frames)  # Asegurarse de que el último proceso llegue hasta el final

    # Mostrar mensaje inicial
    print(f"Procesando video con {num_processes} núcleos...")

    # Crear procesos y recolectar resultados
    pool = multiprocessing.Pool(processes=num_processes)
    results = pool.starmap(procesar_frame_range, [(video_path, log_path, start, end) for start, end in frame_ranges])

    pool.close()
    pool.join()

    # Unir los resultados de todos los procesos
    datos = [item for sublist in results for item in sublist]
    return datos
