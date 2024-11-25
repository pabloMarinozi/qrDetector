import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd

def generar_informe(datos):
    """
    Genera un informe en la consola sobre los códigos QR detectados, incluyendo los 5 más comunes.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
    """
    conteo = Counter([item['data'] for item in datos])
    top_5 = conteo.most_common(5)
    total_distintos = len(conteo)
    print("\nInforme: Los 5 códigos QR más detectados")
    for data, count in top_5:
        print(f"Data: {data}, Veces detectado: {count}")
    print(f"\nCantidad total de códigos QR distintos detectados: {total_distintos}")

def generar_grafico_distribucion(datos, output_path="output/distribucion_qr.png"):
    """
    Genera un gráfico de barras que muestra la distribución de la frecuencia de los códigos QR detectados y lo guarda en un archivo.

    Args:
        datos (list): Lista de diccionarios con información sobre los códigos QR detectados.
        output_path (str): Ruta del archivo de salida para el gráfico.
    """
    conteo = Counter([item['data'] for item in datos])

    # Convertir las etiquetas a enteros si es posible y ordenar según su valor numérico
    etiquetas, valores = zip(*sorted(conteo.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]))

    plt.figure(figsize=(10, 6))
    plt.bar(etiquetas, valores)
    plt.xlabel('Código QR')
    plt.ylabel('Frecuencia')
    plt.title('Distribución de la Frecuencia de los Códigos QR Detectados')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def generar_grafico_temporal(datos, output_path="output/temporal_qr.png"):
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
