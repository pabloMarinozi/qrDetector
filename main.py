import os
import click
import video_qr_processing as pyzbar_video_processing
import video_qr_processing_hybrid as hybrid_video_processing
from utils import generar_csv, generar_video_con_qr
from reporting import generar_informe, generar_grafico_distribucion, generar_grafico_temporal


@click.command()
@click.option('--output-path', type=str, default="output/", help='Ruta del archivo de video de salida con los recuadros de los QR detectados (si se genera)')
@click.option('--video-path', required=True, type=str, help='Ruta al archivo de video')
@click.option('--salida-csv', required=True, type=str, help='Ruta al archivo CSV de salida')
@click.option('--log-path', required=True, type=str, help='Ruta al archivo de log para errores')
@click.option('--num-processes', required=False, type=int, default=4, help='Número de procesos para la ejecución paralela')
@click.option('--generar-video', is_flag=True, help='Indica si se debe generar un video con los recuadros de los códigos QR detectados')
@click.option('--output-video', type=str, default="output_video.mp4", help='Ruta del archivo de video de salida con los recuadros de los QR detectados (si se genera)')
@click.option('--factor-lentitud', type=float, default=0.5, help='Factor para ralentizar el video (menor a 1 lo hará más lento, mayor a 1 lo hará más rápido)')
@click.option('--modo', type=click.Choice(['pyzbar', 'hibrido'], case_sensitive=False), default='hibrido', help='Modo de procesamiento: pyzbar o híbrido')
def main(output_path:str, video_path: str, salida_csv: str, log_path: str, num_processes: int, generar_video: bool, output_video: str, factor_lentitud: float, modo: str):

    os.makedirs(output_path, exist_ok=True)

    # Procesar el video y generar CSV
    if modo == 'hibrido':
        datos = hybrid_video_processing.procesar_video_parallel(video_path, output_path+log_path, output_path, num_processes)
    elif modo == 'pyzbar':
        datos = pyzbar_video_processing.procesar_video_pyzbar(video_path, output_path+log_path, num_processes)
    else:
        raise ValueError("Modo de procesamiento no válido. Use 'pyzbar' o 'hibrido'.")

    generar_csv(datos, output_path+salida_csv)

    # Generar informe y gráficos
    generar_informe(datos)
    generar_grafico_temporal(datos)
    generar_grafico_distribucion(datos)

    # Si se indica, generar el video con los recuadros de los códigos QR detectados
    if generar_video:
        print("Generando el video con los recuadros de los códigos QR detectados...")
        generar_video_con_qr(video_path, datos, output_path+output_video, factor_lentitud)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method("spawn")
    main()

