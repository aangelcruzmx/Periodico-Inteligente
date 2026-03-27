import json
import os
from pathlib import Path
from datetime import datetime


# Carpeta raíz donde se guardarán los artículos clasificados
CARPETA_BASE = Path("data/articulos")


def crear_estructura_carpetas(base: Path = CARPETA_BASE):
    """
    Crea la estructura de carpetas por categoría e idioma si no existe.
    Ejemplo: data/articulos/politica/es/
    """
    categorias = ["deportes", "politica", "economia", "tecnologia", "cultura", "otros"]
    idiomas = ["es", "en", "otros"]

    carpetas_creadas = []
    for categoria in categorias:
        for idioma in idiomas:
            carpeta = base / categoria / idioma
            carpeta.mkdir(parents=True, exist_ok=True)
            carpetas_creadas.append(str(carpeta))

    return carpetas_creadas


def nombre_fichero_seguro(titulo: str, fecha: str) -> str:
    """
    Genera un nombre de fichero seguro a partir del título y la fecha.
    Elimina caracteres especiales y limita la longitud.
    """
    # Limpiar caracteres no permitidos en nombres de fichero
    caracteres_no_validos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\t']
    nombre = titulo
    for c in caracteres_no_validos:
        nombre = nombre.replace(c, '_')

    # Limitar longitud y añadir fecha
    nombre = nombre[:60].strip()
    fecha_limpia = fecha.replace(":", "-").replace(" ", "_")
    return f"{fecha_limpia}_{nombre}.json"


def guardar_articulo(noticia: dict, base: Path = CARPETA_BASE) -> str:
    """
    Guarda una noticia como fichero JSON en la carpeta correspondiente
    según su categoría e idioma.
    Devuelve la ruta donde se guardó.
    """
    categoria = noticia.get("categoria", "otros")
    codigo_idioma = noticia.get("codigo_idioma", "otros")

    # Normalizar idioma a carpeta
    if codigo_idioma not in ["es", "en"]:
        codigo_idioma = "otros"

    # Construir ruta destino
    carpeta_destino = base / categoria / codigo_idioma
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    nombre = nombre_fichero_seguro(
        titulo=noticia.get("titulo", "sin_titulo"),
        fecha=noticia.get("fecha_scraping", datetime.now().strftime("%Y-%m-%d %H:%M"))
    )

    ruta_fichero = carpeta_destino / nombre

    with open(ruta_fichero, "w", encoding="utf-8") as f:
        json.dump(noticia, f, ensure_ascii=False, indent=2)

    return str(ruta_fichero)


def clasificar_noticias(noticias_analizadas: list[dict], base: Path = CARPETA_BASE) -> dict:
    """
    Función principal: recibe la lista de noticias ya analizadas por Azure
    y las distribuye en carpetas según categoría e idioma.

    Devuelve un resumen con cuántos artículos fueron a cada carpeta.
    """
    crear_estructura_carpetas(base)

    resumen = {}
    rutas_guardadas = []

    for noticia in noticias_analizadas:
        ruta = guardar_articulo(noticia, base)
        rutas_guardadas.append(ruta)

        # Acumular estadísticas
        categoria = noticia.get("categoria", "otros")
        idioma = noticia.get("codigo_idioma", "otros")
        clave = f"{categoria}/{idioma}"
        resumen[clave] = resumen.get(clave, 0) + 1

    return {
        "total": len(rutas_guardadas),
        "distribucion": resumen,
        "rutas": rutas_guardadas
    }


def listar_articulos(base: Path = CARPETA_BASE) -> dict:
    """
    Recorre la estructura de carpetas y devuelve un inventario
    de todos los artículos guardados, agrupados por categoría.
    """
    inventario = {}

    if not base.exists():
        return inventario

    for categoria_dir in sorted(base.iterdir()):
        if not categoria_dir.is_dir():
            continue
        categoria = categoria_dir.name
        inventario[categoria] = {}

        for idioma_dir in sorted(categoria_dir.iterdir()):
            if not idioma_dir.is_dir():
                continue
            ficheros = list(idioma_dir.glob("*.json"))
            if ficheros:
                inventario[categoria][idioma_dir.name] = len(ficheros)

    return inventario
