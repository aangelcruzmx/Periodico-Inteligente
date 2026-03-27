import json
import os
from pathlib import Path
from dotenv import load_dotenv

from src.scraper_elpais import obtener_noticias_portada, guardar_noticias
from src.scraper_20minutos import obtener_noticias_portada as obtener_20min
from src.api_newsdata import obtener_noticias_newsdata
from src.api_newsapi import obtener_noticias_newsapi
from src.azure_language import crear_cliente, analizar_noticias
from src.clasificador import clasificar_noticias
from src.azure_speech import generar_podcast_multifuente
from src.azure_translator import traducir_noticia


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _recopilar_noticias(fuentes: dict, max_noticias: int = 10):
    """
    Recopila noticias de las fuentes activadas.
    fuentes: dict con claves 'elpais', '20minutos', 'newsdata', 'newsapi' → bool
    Cada fuente se ejecuta en un try/except para que un fallo no bloquee las demás.
    Devuelve (lista_noticias, lista_avisos).
    """
    todas = []
    avisos = []

    if fuentes.get("elpais", True):
        try:
            todas += obtener_noticias_portada(max_noticias=max_noticias)
        except Exception as e:
            avisos.append(f"El País falló: {e}")

    if fuentes.get("20minutos", True):
        try:
            todas += obtener_20min(max_noticias=max_noticias)
        except Exception as e:
            avisos.append(f"20 Minutos falló: {e}")

    if fuentes.get("newsdata", True):
        newsdata_key = os.getenv("NEWSDATA_KEY")
        if newsdata_key:
            try:
                todas += obtener_noticias_newsdata(api_key=newsdata_key, max_noticias=max_noticias)
            except Exception as e:
                avisos.append(f"NewsData falló: {e}")
        else:
            avisos.append("NewsData: falta NEWSDATA_KEY en .env")

    if fuentes.get("newsapi", True):
        newsapi_key = os.getenv("NEWSAPI_KEY")
        if newsapi_key:
            try:
                todas += obtener_noticias_newsapi(api_key=newsapi_key, max_noticias=max_noticias)
            except Exception as e:
                avisos.append(f"NewsAPI falló: {e}")
        else:
            avisos.append("NewsAPI: falta NEWSAPI_KEY en .env")

    return todas, avisos


def ejecutar_pipeline(
    generar_audio: bool = True,
    traducir: bool = True,
    max_noticias: int = 10,
    fuentes: dict | None = None,
    podcast_idiomas: list[str] | None = None,
):
    """
    Ejecuta el pipeline completo:
      1. Recopilación de noticias (4 fuentes)
      2. Análisis con Azure Language
      3. Traducción de noticias en inglés (opcional)
      4. Clasificación en carpetas
      5. (Opcional) Generación del podcast multi-fuente con Azure Speech

    Devuelve un dict con el resumen de cada paso.
    Lanza excepciones si algo falla.
    """
    if podcast_idiomas is None:
        podcast_idiomas = ["es", "en"]
    if fuentes is None:
        fuentes = {"elpais": True, "20minutos": True, "newsdata": True, "newsapi": True}

    resultado = {}

    # ── 1. Recopilación ───────────────────────────────────────────────────
    yield "scraping", "Recopilando noticias de todas las fuentes..."
    noticias, avisos = _recopilar_noticias(fuentes, max_noticias=max_noticias)
    guardar_noticias(noticias, ruta=str(ROOT / "data" / "noticias_hoy.json"))
    resultado["scraping"] = len(noticias)
    resultado["avisos"] = avisos

    if avisos:
        yield "aviso", f"⚠️ Algunas fuentes fallaron: {'; '.join(avisos)}"

    if not noticias:
        raise RuntimeError("No se obtuvieron noticias de ninguna fuente.")

    # ── 2. Análisis con Azure Language ────────────────────────────────────
    yield "analisis", "Analizando noticias con Azure Language..."
    language_key = os.getenv("LANGUAGE_KEY")
    language_endpoint = os.getenv("LANGUAGE_ENDPOINT")

    if not language_key or not language_endpoint:
        raise RuntimeError("Faltan LANGUAGE_KEY o LANGUAGE_ENDPOINT en el .env")

    cliente = crear_cliente(endpoint=language_endpoint, key=language_key)
    noticias_analizadas = analizar_noticias(cliente, noticias)
    resultado["analisis"] = len(noticias_analizadas)

    # Guardar JSON de noticias analizadas
    ruta_json = ROOT / "data" / "noticias_analizadas.json"
    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(noticias_analizadas, f, ensure_ascii=False, indent=2)

    # ── 3. Traducción de noticias en inglés (opcional) ─────────────────────
    if traducir:
        noticias_en = [n for n in noticias_analizadas if n.get("codigo_idioma") != "es"]
        if noticias_en:
            translator_key = os.getenv("TRANSLATOR_KEY")
            translator_region = os.getenv("TRANSLATOR_REGION")
            translator_endpoint = os.getenv("TRANSLATOR_ENDPOINT")

            if translator_key and translator_region and translator_endpoint:
                yield "traduccion", f"Traduciendo {len(noticias_en)} noticias en inglés..."
                traducidas = 0
                for n in noticias_en:
                    try:
                        traducir_noticia(n, translator_key, translator_region, translator_endpoint)
                        traducidas += 1
                    except Exception as e:
                        resultado.setdefault("avisos", []).append(
                            f"Traducción falló para '{n.get('titulo', '?')[:40]}': {e}"
                        )
                resultado["traduccion"] = traducidas
            else:
                resultado.setdefault("avisos", []).append(
                    "Traducción omitida: faltan TRANSLATOR_KEY, TRANSLATOR_REGION o TRANSLATOR_ENDPOINT en .env"
                )
                yield "aviso", "⚠️ Traducción omitida: faltan claves del Translator en .env"

    # Guardar JSON actualizado (con traducciones si las hay)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(noticias_analizadas, f, ensure_ascii=False, indent=2)

    # ── 4. Clasificación en carpetas ──────────────────────────────────────
    yield "clasificacion", "Clasificando artículos en carpetas..."
    resumen_clas = clasificar_noticias(
        noticias_analizadas, base=ROOT / "data" / "articulos"
    )
    resultado["clasificacion"] = resumen_clas["total"]

    # ── 5. Podcast multi-fuente (opcional) ────────────────────────────────
    if generar_audio:
        speech_key = os.getenv("SPEECH_KEY")
        speech_region = os.getenv("SPEECH_REGION")

        if not speech_key or not speech_region:
            raise RuntimeError("Faltan SPEECH_KEY o SPEECH_REGION en el .env")

        resultado["podcast"] = {}
        carpeta_salida = str(ROOT / "output")

        for idioma in podcast_idiomas:
            # Podcast EN solo si hay noticias en inglés
            if idioma == "en":
                hay_en = any(n.get("codigo_idioma") == "en" for n in noticias_analizadas)
                if not hay_en:
                    continue

            yield "podcast", f"Generando podcast en {idioma.upper()} con Azure Speech..."
            ruta_audio = generar_podcast_multifuente(
                noticias=noticias_analizadas,
                speech_key=speech_key,
                speech_region=speech_region,
                idioma=idioma,
                carpeta_salida=carpeta_salida,
            )
            resultado["podcast"][idioma] = ruta_audio

    yield "completado", resultado
