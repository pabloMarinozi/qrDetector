import cv2
import pandas as pd
from pyzbar.pyzbar import decode
import click
import sys
import os
from collections import Counter
import warnings
import multiprocessing
import time
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

def mide_tiempo(funcion):
    def funcion_medida(*args, **kwargs):
        inicio = time.time()
        c = funcion(*args, **kwargs)
        print(time.time() - inicio)
        return c
    return funcion_medida


def procesar_frame_range(video_path: str, log_path: str, start_frame: int, end_frame: int, progreso):
    """
    Procesa un rango de frames de un video para detectar códigos QR.

    Args:
        video_path (str): Ruta al archivo de video.
        log_path (str): Ruta al archivo de log para registrar errores.
        start_frame (int): Frame inicial para comenzar el procesamiento.
        end_frame (int): Frame final hasta donde se debe procesar.
        progreso (multiprocessing.Value): Valor compartido para el seguimiento del progreso.

    Returns:
        list: Lista de diccionarios con información sobre los códigos QR detectados.
    """
    datos = []
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frame_num = start_frame

    # Redirigir stderr al archivo de log
    stderr_fileno = sys.stderr.fileno()
    with open(log_path, 'a') as log_file:
        os.dup2(log_file.fileno(), stderr_fileno)

        while frame_num < end_frame and cap.isOpened():
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
            # Actualizar el progreso compartido solo cuando se completa un cuarto del total de frames
            if (frame_num - start_frame) % ((end_frame - start_frame) // 4) == 0:
                progreso.value += (end_frame - start_frame) // 4

    cap.release()
    return datos

@mide_tiempo
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

    # Crear un valor compartido para el progreso
    with multiprocessing.Manager() as manager:
        progreso = manager.Value('i', 0)
        pool = multiprocessing.Pool(processes=num_processes)
        results = pool.starmap_async(procesar_frame_range, [(video_path, log_path, start, end, progreso) for start, end in frame_ranges])

        # Mostrar progreso en vivo
        while not results.ready():
            porcentaje = (progreso.value / total_frames) * 100
            sys.stdout.write(f'\rProcesando: {porcentaje:.2f}%')
            sys.stdout.flush()
            time.sleep(0.5)

        # Esperar a que todos los procesos terminen
        pool.close()
        pool.join()

        # Unir los resultados de todos los procesos
        datos = [item for sublist in results.get() for item in sublist]
    return datos

def generar_csv(datos, salida_csv: str):
    """
    Genera un archivo CSV con los datos de los códigos QR detectados.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
        salida_csv (str): Ruta del archivo CSV de salida.
    """
    # Guardar datos en un archivo CSV ordenados por la columna 'data'
    df = pd.DataFrame(datos)
    df = df.sort_values(by='data')
    df.to_csv(salida_csv, index=False)
    print(f'Datos guardados en {salida_csv}')

def generar_informe(datos):
    """
    Genera un informe en la consola sobre los códigos QR detectados, incluyendo los 5 más comunes.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
    """
    # Contar la cantidad de veces que aparece cada QR
    conteo = Counter([item['data'] for item in datos])
    top_5 = conteo.most_common(5)
    total_distintos = len(conteo)
    print("\nInforme: Los 5 códigos QR más detectados")
    for data, count in top_5:
        print(f"Data: {data}, Veces detectado: {count}")
    print(f"\nCantidad total de códigos QR distintos detectados: {total_distintos}")



def generar_grafico_distribucion(datos, output_path="distribucion_qr.png"):
    """
    Genera un gráfico de barras que muestra la distribución de la frecuencia de los códigos QR detectados y lo guarda en un archivo.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
        output_path (str): Ruta del archivo de salida para el gráfico.
    """
    conteo = Counter([item['data'] for item in datos])
    etiquetas = list(conteo.keys())
    valores = list(conteo.values())

    plt.figure(figsize=(10, 6))
    plt.bar(etiquetas, valores)
    plt.xlabel('Código QR')
    plt.ylabel('Frecuencia')
    plt.title('Distribución de la Frecuencia de los Códigos QR Detectados')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def generar_grafico_temporal(datos, output_path="temporal_qr.png"):
    """
    Genera un gráfico de líneas que muestra la cantidad de códigos QR detectados a lo largo de los frames del video y lo guarda en un archivo.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
        output_path (str): Ruta del archivo de salida para el gráfico.
    """
    df = pd.DataFrame(datos)
    df_grouped = df.groupby('frame')['data'].count().reset_index()

    plt.figure(figsize=(10, 6))
    plt.plot(df_grouped['frame'], df_grouped['data'])
    plt.xlabel('Número de Frame')
    plt.ylabel('Cantidad de Códigos QR Detectados')
    plt.title('Detección de Códigos QR a lo Largo del Video')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def generar_informe_detallado(datos):
    """
    Genera un informe detallado en la consola sobre la cantidad de veces que se detectó cada código QR.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
    """
    conteo = Counter([item['data'] for item in datos])
    print("\nInforme Completo de los Códigos QR Detectados")
    for data, count in conteo.items():
        print(f"Data: {data}, Veces detectado: {count}")

@click.command()
@click.option('--video-path', required=True, type=str, help='Ruta al archivo de video')
@click.option('--salida-csv', required=True, type=str, help='Ruta al archivo CSV de salida')
@click.option('--log-path', required=True, type=str, help='Ruta al archivo de log para errores')
@click.option('--num-processes', required=False, type=int, default=4, help='Número de procesos para la ejecución paralela')
def main(video_path: str, salida_csv: str, log_path: str, num_processes: int):
    """
    Función principal que coordina la ejecución del procesamiento del video, la generación del CSV y el informe.

    Args:
        video_path (str): Ruta al archivo de video.
        salida_csv (str): Ruta del archivo CSV de salida.
        log_path (str): Ruta al archivo de log para registrar errores.
        num_processes (int): Número de procesos a utilizar para la ejecución paralela.
    """
    datos = procesar_video_parallel(video_path, log_path, num_processes)
    generar_csv(datos, salida_csv)
    generar_informe(datos)
    generar_grafico_temporal(datos)
    generar_grafico_distribucion(datos)

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
