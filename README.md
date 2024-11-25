# Proyecto de Procesamiento de Códigos QR en Videos

Este repositorio contiene una herramienta para detectar códigos QR en videos y generar informes y visualizaciones a partir de la información recolectada. Utiliza diversas técnicas, incluyendo procesamiento de video paralelo y enfoques híbridos para mejorar la precisión de detección.

## Características Principales

- **Detección de Códigos QR en Videos**: Permite procesar videos y detectar códigos QR en cada uno de los frames. La detección se realiza utilizando bibliotecas como OpenCV y pyzbar.
- **Procesamiento Paralelo**: Utiliza procesamiento paralelo para mejorar la eficiencia en el análisis de videos grandes, aprovechando múltiples núcleos del procesador.
- **Informes y Visualizaciones**: Genera informes con los códigos QR más comunes detectados, así como gráficos que muestran la distribución temporal y la frecuencia de detección.
- **Generación de Video**: Genera un video con los recuadros de los códigos QR detectados destacados en cada frame.

## Archivos Principales

- `main.py`: Archivo principal que gestiona la ejecución del procesamiento de video, la generación del CSV de resultados, los informes y las visualizaciones.
- `video_qr_processing.py` y `video_qr_processing_hybrid.py`: Módulos para procesar videos y detectar códigos QR, con soporte para procesamiento paralelo. El enfoque "híbrido" mejora la precisión mediante técnicas adicionales de segmentación.
- `utils.py`: Contiene funciones auxiliares, incluyendo generación de archivos CSV y de videos con los códigos QR detectados.
- `reporting.py`: Módulo para generar informes en consola y gráficos de visualización sobre los códigos QR detectados.
- `detectar_qr.py` y `detectar_qr_parallel.py`: Scripts para la detección de códigos QR en videos, con versiones secuenciales y paralelas.

## Instalación

1. Clona este repositorio:
   ```sh
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DEL_REPOSITORIO>
   ```
2. Instala los requisitos:
   ```sh
   pipenv install
   ```

## Uso

Puedes ejecutar el script principal (`main.py`) desde la línea de comandos con varias opciones disponibles:

```sh
python main.py --video-path <ruta_al_video> --salida-csv <ruta_csv_salida> --log-path <ruta_log> [opciones]
```

### Opciones Principales

- `--video-path`: Ruta al archivo de video que deseas procesar (obligatorio).
- `--salida-csv`: Ruta del archivo CSV donde se guardarán los resultados (obligatorio).
- `--log-path`: Ruta del archivo de log para registrar errores (obligatorio).
- `--num-processes`: Número de procesos a utilizar para el procesamiento paralelo (opcional, por defecto: 4).
- `--generar-video`: Indicador para generar un video de salida con los códigos QR detectados (opcional).
- `--modo`: Selecciona el modo de procesamiento (`pyzbar` o `hibrido`) (opcional, por defecto: `hibrido`).

### Ejemplo de Ejecución

```sh
pipenv shell
python main.py --video-path input/video.mp4 --salida-csv output/datos.csv --log-path output/log.txt --num-processes 4 --generar-video --output-video output_video.mp4 --modo hibrido
```

## Informes y Visualizaciones

El script generará diferentes tipos de resultados:

- **CSV con los datos detectados**: Un archivo CSV que contiene información detallada sobre cada código QR detectado (frame, datos, coordenadas).
- **Informe en Consola**: Un informe con los 5 códigos QR más comunes detectados.
- **Gráficos de Distribución y Temporalidad**: Gráficos que muestran la frecuencia de detección de los códigos QR y su distribución a lo largo del video.

## Requisitos

- Python 3.7 o superior
- Bibliotecas necesarias: OpenCV, pyzbar, pandas, matplotlib, numpy, click

Puedes instalar estas bibliotecas ejecutando:

```sh
pipenv install
```

\



