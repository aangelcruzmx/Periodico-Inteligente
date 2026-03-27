from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential


# ── Categorías reconocidas para clasificar artículos en carpetas ──────────────
CATEGORIAS_VALIDAS = {
    "deportes", "politica", "economia", "tecnologia", "cultura", "otros"
}

# Mapa de palabras clave → categoría (fallback si Azure no detecta bien)
KEYWORDS_CATEGORIA = {
    "deportes":   ["fútbol", "baloncesto", "deporte", "liga", "partido", "atleta", "olimpiadas"],
    "politica":   ["gobierno", "presidente", "elecciones", "partido", "congreso", "senado", "ley"],
    "economia":   ["bolsa", "euro", "pib", "inflación", "mercado", "empresa", "inversión", "banco"],
    "tecnologia": ["inteligencia artificial", "tecnología", "software", "startup", "digital", "ciberseguridad"],
    "cultura":    ["cine", "música", "arte", "teatro", "libro", "exposición", "festival", "literatura"],
}


def crear_cliente(endpoint: str, key: str) -> TextAnalyticsClient:
    """Crea y devuelve un cliente de Azure Text Analytics."""
    credential = AzureKeyCredential(key)
    return TextAnalyticsClient(endpoint=endpoint, credential=credential)


def detectar_idioma(cliente: TextAnalyticsClient, textos: list[str], batch_size: int = 10) -> list[dict]:
    """
    Detecta el idioma de una lista de textos.
    Devuelve una lista de dicts con 'idioma' y 'confianza'.
    Procesa en lotes de batch_size para respetar el límite de la API.
    """
    resultados = []
    for inicio in range(0, len(textos), batch_size):
        lote = textos[inicio:inicio + batch_size]
        respuesta = cliente.detect_language(documents=lote)
        for doc in respuesta:
            if not doc.is_error:
                resultados.append({
                    "idioma": doc.primary_language.name,
                    "codigo": doc.primary_language.iso6391_name,
                    "confianza": round(doc.primary_language.confidence_score, 2)
                })
            else:
                resultados.append({"idioma": "desconocido", "codigo": "unk", "confianza": 0.0})
    return resultados


def extraer_frases_clave(cliente: TextAnalyticsClient, textos: list[str], batch_size: int = 10) -> list[list[str]]:
    """
    Extrae frases clave de una lista de textos.
    Devuelve una lista de listas de frases.
    Procesa en lotes de batch_size para respetar el límite de la API.
    """
    resultados = []
    for inicio in range(0, len(textos), batch_size):
        lote = textos[inicio:inicio + batch_size]
        respuesta = cliente.extract_key_phrases(documents=lote)
        for doc in respuesta:
            if not doc.is_error:
                resultados.append(list(doc.key_phrases))
            else:
                resultados.append([])
    return resultados


def analizar_sentimiento(cliente: TextAnalyticsClient, textos: list[str], batch_size: int = 10) -> list[dict]:
    """
    Analiza el sentimiento de una lista de textos.
    Devuelve 'positivo', 'negativo', 'neutro' o 'mixto' con puntuaciones.
    Procesa en lotes de batch_size para respetar el límite de la API.
    """
    resultados = []
    for inicio in range(0, len(textos), batch_size):
        lote = textos[inicio:inicio + batch_size]
        respuesta = cliente.analyze_sentiment(documents=lote)
        for doc in respuesta:
            if not doc.is_error:
                resultados.append({
                    "sentimiento": doc.sentiment,
                    "positivo":  round(doc.confidence_scores.positive, 2),
                    "neutro":    round(doc.confidence_scores.neutral, 2),
                    "negativo":  round(doc.confidence_scores.negative, 2),
                })
            else:
                resultados.append({"sentimiento": "desconocido", "positivo": 0, "neutro": 0, "negativo": 0})
    return resultados


def inferir_categoria(titulo: str, frases_clave: list[str], seccion_url: str) -> str:
    """
    Intenta inferir la categoría del artículo usando:
    1. La sección extraída de la URL (más fiable)
    2. Palabras clave del título y frases clave de Azure
    3. Fallback a 'otros'
    """
    # 1. Si la sección de la URL ya es una categoría válida
    seccion_limpia = seccion_url.lower().strip()
    for cat in CATEGORIAS_VALIDAS:
        if cat in seccion_limpia:
            return cat

    # 2. Buscar palabras clave en título y frases
    texto_combinado = (titulo + " " + " ".join(frases_clave)).lower()
    for categoria, keywords in KEYWORDS_CATEGORIA.items():
        if any(kw in texto_combinado for kw in keywords):
            return categoria

    return "otros"


def analizar_noticias(cliente: TextAnalyticsClient, noticias: list[dict]) -> list[dict]:
    """
    Función principal: recibe la lista de noticias del scraper
    y devuelve cada noticia enriquecida con el análisis de Azure.
    
    Procesa en lotes de 10 (límite de la API gratuita).
    """
    textos = [
        f"{n['titulo']}. {n['resumen']}" if n['resumen'] else n['titulo']
        for n in noticias
    ]

    n_lotes = (len(textos) + 9) // 10  # ceil(len/10)
    print(f"  → {len(textos)} documentos en {n_lotes} lote(s) de máx. 10")

    print("  → Detectando idiomas...")
    idiomas = detectar_idioma(cliente, textos)

    print("  → Extrayendo frases clave...")
    frases = extraer_frases_clave(cliente, textos)

    print("  → Analizando sentimiento...")
    sentimientos = analizar_sentimiento(cliente, textos)

    noticias_analizadas = []
    for i, noticia in enumerate(noticias):
        categoria = inferir_categoria(
            titulo=noticia["titulo"],
            frases_clave=frases[i],
            seccion_url=noticia.get("seccion", "otros")
        )
        noticias_analizadas.append({
            **noticia,
            "idioma":       idiomas[i]["idioma"],
            "codigo_idioma": idiomas[i]["codigo"],
            "frases_clave": frases[i],
            "sentimiento":  sentimientos[i]["sentimiento"],
            "score_sentimiento": {
                "positivo": sentimientos[i]["positivo"],
                "neutro":   sentimientos[i]["neutro"],
                "negativo": sentimientos[i]["negativo"],
            },
            "categoria": categoria,
        })

    return noticias_analizadas
