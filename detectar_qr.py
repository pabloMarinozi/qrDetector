import cv2
import pandas as pd
from pyzbar.pyzbar import decode
import click
import sys
import os
from collections import Counter
import warnings
import time

def mide_tiempo(funcion):
    def funcion_medida(*args, **kwargs):
        inicio = time.time()
        c = funcion(*args, **kwargs)
        print(time.time() - inicio)
        return c
    return funcion_medida

warnings.filterwarnings("ignore")

@mide_tiempo
def procesar_video(video_path: str, log_path: str):
    datos = []

    cap = cv2.VideoCapture(video_path)
    frame_num = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Redirigir stderr al archivo de log
    stderr_fileno = sys.stderr.fileno()
    with open(log_path, 'a') as log_file:
        os.dup2(log_file.fileno(), stderr_fileno)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            try:
                qrs = decode(frame)
            except AssertionError as e:
                log_file.write(f'Error en el frame {frame_num}: {str(e)}\n')
                qrs = []

            for qr in qrs:
                try:
                    (x, y, w, h) = qr.rect
                    data = qr.data.decode('utf-8')
                    datos.append({
                        'frame': frame_num,
                        'data': data,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h
                    })
                except Exception as e:
                    # Registrar cualquier error al procesar un QR específico
                    log_file.write(f'Error procesando QR en el frame {frame_num}: {str(e)}\n')
                    continue

            frame_num += 1

            # Mostrar el progreso
            progreso = (frame_num / total_frames) * 100
            sys.stdout.write(f'\rProcesando: {progreso:.2f}%')
            sys.stdout.flush()

    cap.release()
    print()  # Nueva línea después de completar el progreso

    return datos

def generar_csv(datos, salida_csv: str):
    # Guardar datos en un archivo CSV ordenados por la columna 'data'
    df = pd.DataFrame(datos)
    df = df.sort_values(by='data')
    df.to_csv(salida_csv, index=False)
    print(f'Datos guardados en {salida_csv}')

def generar_informe(datos):
    # Contar la cantidad de veces que aparece cada QR
    conteo = Counter([item['data'] for item in datos])
    top_5 = conteo.most_common(5)
    total_distintos = len(conteo)
    print("\nInforme: Los 5 códigos QR más detectados")
    for data, count in top_5:
        print(f"Data: {data}, Veces detectado: {count}")
    print(f"\nCantidad total de códigos QR distintos detectados: {total_distintos}")


@click.command()
@click.option('--video-path', required=True, type=str, help='Ruta al archivo de video')
@click.option('--salida-csv', required=True, type=str, help='Ruta al archivo CSV de salida')
@click.option('--log-path', required=True, type=str, help='Ruta al archivo de log para errores')
def main(video_path: str, salida_csv: str, log_path: str):
    datos = procesar_video(video_path, log_path)
    generar_csv(datos, salida_csv)
    generar_informe(datos)

if __name__ == "__main__":
    main()
