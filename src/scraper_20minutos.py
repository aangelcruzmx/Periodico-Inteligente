import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def _inferir_seccion(href: str) -> str:
    """Extrae la sección de la URL de 20minutos.es."""
    mapa = {
        "deportes": "deportes",
        "tecnologia": "tecnologia",
        "economia": "economia",
        "politica": "politica",
        "internacional": "politica",
        "cultura": "cultura",
        "cine": "cultura",
        "musica": "cultura",
        "television": "cultura",
    }
    partes = href.replace("https://www.20minutos.es/", "").split("/")
    seccion_raw = partes[0].lower() if partes else ""
    return mapa.get(seccion_raw, "otros")


def obtener_noticias_portada(max_noticias: int = 10) -> list[dict]:
    """
    Scrapea la portada de 20minutos.es y devuelve noticias en el formato
    unificado: {titulo, seccion, resumen, url, fecha_scraping, fuente}.
    """
    url = "https://www.20minutos.es/"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    noticias = []

    articulos = soup.find_all("article", limit=max_noticias * 3)

    for articulo in articulos:
        titulo_tag = articulo.find(["h1", "h2", "h3"])
        if not titulo_tag:
            continue

        enlace_tag = titulo_tag.find("a", href=True)
        if not enlace_tag:
            enlace_tag = articulo.find("a", href=True)
        if not enlace_tag:
            continue

        titulo = enlace_tag.get_text(strip=True)
        href = enlace_tag["href"]

        if not titulo:
            continue

        if href.startswith("/"):
            href = "https://www.20minutos.es" + href

        resumen_tag = articulo.find("p")
        resumen = resumen_tag.get_text(strip=True) if resumen_tag else ""

        noticias.append({
            "titulo": titulo,
            "seccion": _inferir_seccion(href),
            "resumen": resumen,
            "url": href,
            "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fuente": "20minutos",
        })

        if len(noticias) >= max_noticias:
            break

    return noticias
