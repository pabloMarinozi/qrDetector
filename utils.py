import pandas as pd
import numpy as np
import time
import cv2
import os

def mide_tiempo(funcion):
    """
    Decorador para medir el tiempo de ejecución de una función.

    Args:
        funcion (callable): La función cuyo tiempo de ejecución se desea medir.

    Returns:
        callable: Una función decorada que imprime el tiempo de ejecución.
    """
    def funcion_medida(*args, **kwargs):
        inicio = time.time()
        c = funcion(*args, **kwargs)
        print(f"Tiempo de ejecución de '{funcion.__name__}': {time.time() - inicio:.2f} segundos")
        return c
    return funcion_medida

def extraer_frames(video_path: str, output_dir: str):
    """
    Extrae todos los frames de un video y los guarda como imágenes en disco.

    Args:
        video_path (str): Ruta al archivo de video.
        output_dir (str): Directorio donde se guardarán los frames.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_num = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = os.path.join(output_dir, f"frame_{frame_num:04d}.png")
        cv2.imwrite(frame_path, frame)
        frame_num += 1

    cap.release()
    print(f"Se han guardado {frame_num} frames en {output_dir}")


def generar_csv(datos, prefijo, salida_csv: str):
    """
    Genera un archivo CSV con los datos de los códigos QR detectados.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
        prefijo (str): prefijo para formar el nombre de cada frame
        salida_csv (str): Ruta del archivo CSV de salida.
    """
    rows = []
    for row in datos:
        for i in range(1, 5):  # Genera x1,y1 hasta x4,y4
            rows.append({
                "image_name": f"{prefijo}_{row['frame']}.png",
                "x": row[f"x{i}"],
                "y": row[f"y{i}"],
                "r": 0,
                "detection": row["detected_by"],
                "track_id": 1000 + int(row["data"]) * 4 + i -1,
                "label": "qr",
                "data": int(row["data"]),
                "esquina": i
            })
    df = pd.DataFrame(rows)
    df = df.sort_values(by=['data', 'image_name', 'esquina'])
    df.to_csv(salida_csv, index=False)

def generar_video_con_qr(video_path: str, datos: list, output_video_path: str, factor_lentitud: float = 0.5):
    """
    Genera un nuevo video dibujando polígonos alrededor de los códigos QR detectados.

    Args:
        video_path (str): Ruta al archivo de video original.
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
        output_video_path (str): Ruta para guardar el video con los recuadros dibujados.
        factor_lentitud (float): Factor para ralentizar el video. Menor a 1 hará que el video sea más lento.
    """
    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    slow_fps = max(1, int(fps * factor_lentitud))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, slow_fps, (frame_width, frame_height))

    qr_data_by_frame = {}
    for item in datos:
        frame_num = item['frame']
        if frame_num not in qr_data_by_frame:
            qr_data_by_frame[frame_num] = []
        qr_data_by_frame[frame_num].append(item)

    frame_num = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num in qr_data_by_frame:
            for qr in qr_data_by_frame[frame_num]:
                pts = [(qr['x1'], qr['y1']), (qr['x2'], qr['y2']),
                       (qr['x3'], qr['y3']), (qr['x4'], qr['y4'])]

                color = (0, 255, 0)
                cv2.polylines(frame, [np.array(pts)], isClosed=True, color=color, thickness=2)

                text = qr['data']
                cv2.putText(frame, text, (pts[0][0], pts[0][1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        out.write(frame)
        frame_num += 1

    cap.release()
    out.release()
    print(f'Video guardado en {output_video_path}')
