import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def obtener_noticias_portada(max_noticias=10):
    """
    Scrapea la portada de elpais.com y devuelve una lista de noticias
    con título, sección, resumen y URL.
    """
    url = "https://elpais.com"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    noticias = []

    articulos = soup.find_all("article", limit=max_noticias * 2)

    for articulo in articulos:
        titulo_tag = articulo.find(["h2", "h3"])
        if not titulo_tag:
            continue
        enlace_tag = titulo_tag.find("a", href=True)
        if not enlace_tag:
            continue

        titulo = enlace_tag.get_text(strip=True)
        href = enlace_tag["href"]

        if href.startswith("/"):
            href = "https://elpais.com" + href

        resumen_tag = articulo.find("p")
        resumen = resumen_tag.get_text(strip=True) if resumen_tag else ""

        partes_url = href.replace("https://elpais.com/", "").split("/")
        seccion = partes_url[0] if partes_url else "otros"

        if titulo and href:
            noticias.append({
                "titulo": titulo,
                "seccion": seccion,
                "resumen": resumen,
                "url": href,
                "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "fuente": "elpais",
            })

        if len(noticias) >= max_noticias:
            break

    return noticias


def obtener_cuerpo_noticia(url):
    """
    Dado el enlace de una noticia, descarga y extrae el cuerpo completo del artículo.
    Útil para mandar texto más rico a Azure Language.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        cuerpo_tag = soup.find("div", class_="a_c") or soup.find("article")
        if not cuerpo_tag:
            return ""

        parrafos = cuerpo_tag.find_all("p")
        texto = " ".join(p.get_text(strip=True) for p in parrafos)
        return texto

    except Exception as e:
        print(f"Error al obtener cuerpo de {url}: {e}")
        return ""


def guardar_noticias(noticias, ruta="data/noticias_hoy.json"):
    """Guarda la lista de noticias en un fichero JSON."""
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)
    print(f"✓ {len(noticias)} noticias guardadas en {ruta}")


if __name__ == "__main__":
    noticias = obtener_noticias_portada(max_noticias=10)
    for i, n in enumerate(noticias, 1):
        print(f"{i}. [{n['seccion'].upper()}] {n['titulo']}")
    guardar_noticias(noticias)
