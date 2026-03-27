import requests
from datetime import datetime

# Mapeo de categorías de NewsData (inglés) → categorías del proyecto
MAPA_CATEGORIAS = {
    "politics": "politica",
    "business": "economia",
    "economics": "economia",
    "sports":   "deportes",
    "technology": "tecnologia",
    "science":  "tecnologia",
    "entertainment": "cultura",
    "world":    "otros",
    "top":      "otros",
    "environment": "otros",
    "health":   "otros",
    "food":     "cultura",
    "tourism":  "cultura",
}


def _mapear_categoria(categorias_raw: list[str] | None) -> str:
    """Convierte las categorías de NewsData al esquema del proyecto."""
    if not categorias_raw:
        return "otros"
    for cat in categorias_raw:
        if cat.lower() in MAPA_CATEGORIAS:
            return MAPA_CATEGORIAS[cat.lower()]
    return "otros"


def obtener_noticias_newsdata(api_key: str, max_noticias: int = 10) -> list[dict]:
    """
    Consulta la API de NewsData.io y devuelve noticias en el formato
    unificado del proyecto: {titulo, seccion, resumen, url, fecha_scraping, fuente}.
    """
    url = "https://newsdata.io/api/1/latest"
    params = {
        "apikey": api_key,
        "language": "en",
        "size": min(max_noticias, 50),
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "success":
        raise RuntimeError(f"NewsData API error: {data}")

    noticias = []
    for item in data.get("results", []):
        titulo = item.get("title")
        if not titulo:
            continue

        noticias.append({
            "titulo": titulo,
            "seccion": _mapear_categoria(item.get("category")),
            "resumen": item.get("description") or "",
            "url": item.get("link", ""),
            "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fuente": "newsdata",
        })

        if len(noticias) >= max_noticias:
            break

    return noticias
