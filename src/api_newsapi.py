import requests
from datetime import datetime, timedelta

# Mapeo de categorías extraídas de la URL de la fuente → categorías del proyecto
KEYWORDS_SECCION = {
    "deportes":   ["sport", "football", "soccer", "basketball", "tennis"],
    "politica":   ["politic", "gobierno", "election"],
    "economia":   ["econom", "business", "financ", "market", "banco", "bolsa"],
    "tecnologia": ["tech", "digital", "cyber", "software", "ai", "robot"],
    "cultura":    ["culture", "entertain", "music", "cinema", "art", "book"],
}


def _inferir_seccion(titulo: str, descripcion: str) -> str:
    """Intenta inferir la sección a partir del contenido."""
    texto = (titulo + " " + descripcion).lower()
    for seccion, keywords in KEYWORDS_SECCION.items():
        if any(kw in texto for kw in keywords):
            return seccion
    return "otros"


def obtener_noticias_newsapi(api_key: str, max_noticias: int = 10) -> list[dict]:
    """
    Consulta /v2/everything de NewsAPI.org en español y devuelve noticias
    en el formato unificado: {titulo, seccion, resumen, url, fecha_scraping, fuente}.
    """
    url = "https://newsapi.org/v2/everything"
    desde = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "apiKey": api_key,
        "language": "es",
        "sortBy": "publishedAt",
        "pageSize": min(max_noticias, 100),
        "from": desde,
        "q": "noticias",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"NewsAPI error: {data.get('message', data)}")

    noticias = []
    for item in data.get("articles", []):
        titulo = item.get("title")
        if not titulo or titulo == "[Removed]":
            continue

        descripcion = item.get("description") or ""

        noticias.append({
            "titulo": titulo,
            "seccion": _inferir_seccion(titulo, descripcion),
            "resumen": descripcion,
            "url": item.get("url", ""),
            "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fuente": "newsapi",
        })

        if len(noticias) >= max_noticias:
            break

    return noticias
