import uuid
import requests


def traducir_noticia(
    noticia: dict,
    translator_key: str,
    translator_region: str,
    translator_endpoint: str,
    idioma_origen: str = "en",
    idioma_destino: str = "es",
) -> dict:
    """
    Traduce el título y resumen de una noticia al español usando Azure Translator v3.0.
    Añade los campos 'titulo_es' y 'resumen_es' a la noticia.
    No modifica los campos originales (titulo y resumen se mantienen en inglés).
    """
    path = "translate"
    constructed_url = translator_endpoint.rstrip("/") + "/" + path

    params = {
        "api-version": "3.0",
        "from": idioma_origen,
        "to": idioma_destino,
    }

    headers = {
        "Ocp-Apim-Subscription-Key": translator_key,
        "Ocp-Apim-Subscription-Region": translator_region,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    body = [
        {"Text": noticia.get("titulo", "")},
        {"Text": noticia.get("resumen", "")},
    ]

    response = requests.post(
        constructed_url, params=params, headers=headers, json=body, timeout=15
    )
    response.raise_for_status()
    data = response.json()

    noticia["titulo_es"] = data[0]["translations"][0]["text"]
    noticia["resumen_es"] = data[1]["translations"][0]["text"] if len(data) > 1 else ""
    return noticia
