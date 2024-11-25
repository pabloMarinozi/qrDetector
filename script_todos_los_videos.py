import os

def encontrar_videos_mp4(ruta_carpeta):
    videos_mp4 = []
    for ruta_actual, subdirectorios, archivos in os.walk(ruta_carpeta):
        for archivo in archivos:
            if archivo.lower().endswith('.mp4'):
                ruta = os.path.join(ruta_actual, archivo)
                print(ruta)
                videos_mp4.append(ruta)
    return videos_mp4

# Especifica la ruta de la carpeta donde deseas buscar
ruta_carpeta = "D:/2023-03-20_Costa_de_Araujo"

videos_encontrados = encontrar_videos_mp4(ruta_carpeta)
with open("videos_encontrados.txt", "w") as archivo_salida:
    for video in videos_encontrados:
        archivo_salida.write(video + "\n")
