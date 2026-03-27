import azure.cognitiveservices.speech as speechsdk
from pathlib import Path
from datetime import datetime


def crear_sintetizador(speech_key: str, speech_region: str, fichero_salida: str):
    """
    Crea y devuelve un sintetizador de voz configurado para
    guardar el audio directamente en un fichero MP3.
    """
    config_speech = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=speech_region
    )

    # Voz neuronal 
    # voces disponibles: https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=tts
    config_speech.speech_synthesis_voice_name = "es-MX-Ximena:DragonHDLatestNeural"

    config_speech.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    config_audio = speechsdk.audio.AudioOutputConfig(filename=fichero_salida)

    return speechsdk.SpeechSynthesizer(
        speech_config=config_speech,
        audio_config=config_audio
    )


def _transicion(posicion: int, es_ultima: bool) -> str:
    """
    Devuelve una frase de transición según la posición de la noticia
    dentro de su bloque de categoría.

    posicion 0  → sin transición (el bloque ya abre con "En {categoría}...")
    posicion 1  → "También..." / "Asimismo..."
    posicion 2  → "Además..." / "Por otro lado..."
    posicion 3+ → "Y por último en esta sección..." si es la última, si no "Igualmente..."
    """
    if posicion == 0:
        return ""
    if posicion == 1:
        return "También, "
    if posicion == 2:
        return "Además, "
    if es_ultima:
        return "Y para cerrar esta sección, "
    return "Igualmente, "


def construir_texto_podcast(noticias_analizadas: list[dict]) -> str:
    """
    Construye un texto redactado como presentador de radio.
    Usa solo los titulares — las frases clave se reservan para Streamlit.
    Las transiciones entre noticias de la misma categoría suenan naturales.

    Para noticias en inglés:
      - Si tienen titulo_es (traducidas) → se usa la traducción
      - Si no → se omiten del podcast en español
    """
    ahora = datetime.now()
    dia_semana = ["lunes", "martes", "miércoles", "jueves",
                  "viernes", "sábado", "domingo"][ahora.weekday()]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_str = f"{dia_semana} {ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"

    # Filtrar: solo noticias en español o traducidas al español
    noticias_podcast = []
    for n in noticias_analizadas:
        idioma = n.get("codigo_idioma", "es")
        if idioma == "es":
            noticias_podcast.append(n)
        elif n.get("titulo_es"):
            noticias_podcast.append(n)

    # Agrupar noticias por categoría respetando el orden original
    por_categoria = {}
    for n in noticias_podcast:
        cat = n.get("categoria", "otros")
        por_categoria.setdefault(cat, []).append(n)

    partes = []

    # Introducción
    partes.append(
        f"Bienvenidos al resumen del día. Hoy es {fecha_str}. "
        f"A continuación, las noticias más importantes."
    )

    nombres_categoria = {
        "politica":   "Política",
        "economia":   "Economía",
        "deportes":   "Deportes",
        "tecnologia": "Tecnología",
        "cultura":    "Cultura",
        "otros":      "Otras noticias",
    }

    for categoria, nombre in nombres_categoria.items():
        noticias_cat = por_categoria.get(categoria, [])
        if not noticias_cat:
            continue

        # Abre el bloque con la categoría
        partes.append(f"En {nombre}.")

        total = len(noticias_cat)
        for i, n in enumerate(noticias_cat):
            titulo = n.get("titulo_es") or n.get("titulo", "")
            es_ultima = (i == total - 1) and (total > 1)
            transicion = _transicion(i, es_ultima)
            partes.append(f"{transicion}{titulo}.")

    # Cierre
    partes.append(
        "Esto ha sido el resumen de noticias del día. "
        "Gracias por escucharnos y hasta mañana."
    )

    return " ".join(partes)


def generar_podcast(
    noticias_analizadas: list[dict],
    speech_key: str,
    speech_region: str,
    carpeta_salida: str = "output"
) -> str:
    """
    Construye el texto del podcast, lo convierte a voz con Azure Speech
    y guarda el fichero MP3. Devuelve la ruta del fichero generado.
    """
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d")
    fichero_salida = str(Path(carpeta_salida) / f"podcast_{fecha}.mp3")

    print("  → Construyendo texto del podcast...")
    texto = construir_texto_podcast(noticias_analizadas)
    print(f"  → Texto generado ({len(texto)} caracteres)")
    print("  → Convirtiendo a voz con Azure Speech...")

    sintetizador = crear_sintetizador(speech_key, speech_region, fichero_salida)
    resultado = sintetizador.speak_text_async(texto).get()

    if resultado.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"  ✓ Audio generado: {fichero_salida}")
        return fichero_salida
    elif resultado.reason == speechsdk.ResultReason.Canceled:
        detalles = speechsdk.CancellationDetails.from_result(resultado)
        raise RuntimeError(f"Error en Speech: {detalles.reason} — {detalles.error_details}")

    return fichero_salida


def _nombre_fuente(fuente: str) -> str:
    """Devuelve el nombre legible de una fuente."""
    nombres = {
        "elpais": "El País",
        "20minutos": "20 Minutos",
        "newsdata": "NewsData",
        "newsapi": "NewsAPI",
    }
    return nombres.get(fuente, fuente)


def construir_texto_podcast_multifuente(
    noticias: list[dict],
    idioma: str = "es",
) -> str:
    """
    Construye un texto de podcast organizado por FUENTE (El País, 20 Minutos, etc.).
    Dentro de cada fuente, agrupa por categoría.

    idioma:
      - "es" → podcast en español. Usa titulo_es si existe, si no titulo.
              Omite noticias en inglés sin traducción.
      - "en" → podcast en inglés. Solo incluye noticias cuyo codigo_idioma == "en".
              Usa titulo original (en inglés).
    """
    ahora = datetime.now()

    if idioma == "es":
        dia_semana = ["lunes", "martes", "miércoles", "jueves",
                      "viernes", "sábado", "domingo"][ahora.weekday()]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        fecha_str = f"{dia_semana} {ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"

        # Filtrar noticias válidas para español
        noticias_validas = []
        for n in noticias:
            cod = n.get("codigo_idioma", "es")
            if cod == "es":
                noticias_validas.append(n)
            elif n.get("titulo_es"):
                noticias_validas.append(n)
    else:
        dias_en = ["Monday", "Tuesday", "Wednesday", "Thursday",
                   "Friday", "Saturday", "Sunday"]
        fecha_str = f"{dias_en[ahora.weekday()]}, {ahora.strftime('%B')} {ahora.day}, {ahora.strftime('%Y')}"

        noticias_validas = [n for n in noticias if n.get("codigo_idioma") == "en"]

    if not noticias_validas:
        if idioma == "es":
            return "No hay noticias disponibles para generar el podcast en español."
        return "No news available to generate the English podcast."

    # Agrupar por fuente
    por_fuente = {}
    for n in noticias_validas:
        fuente = n.get("fuente", "elpais")
        por_fuente.setdefault(fuente, []).append(n)

    nombres_categoria = {
        "politica":   ("Política", "Politics"),
        "economia":   ("Economía", "Economy"),
        "deportes":   ("Deportes", "Sports"),
        "tecnologia": ("Tecnología", "Technology"),
        "cultura":    ("Cultura", "Culture"),
        "otros":      ("Otras noticias", "Other news"),
    }

    partes = []

    # Introducción
    n_fuentes = len(por_fuente)
    fuentes_txt = ", ".join(_nombre_fuente(f) for f in por_fuente)
    if idioma == "es":
        partes.append(
            f"Bienvenidos al resumen del día. Hoy es {fecha_str}. "
            f"Hemos recopilado noticias de {n_fuentes} fuentes: {fuentes_txt}. "
            f"A continuación, las noticias más importantes."
        )
    else:
        partes.append(
            f"Welcome to today's news summary. Today is {fecha_str}. "
            f"We've gathered news from {n_fuentes} sources: {fuentes_txt}. "
            f"Here are the most important headlines."
        )

    # Orden de fuentes: elpais, 20minutos, newsapi, newsdata
    orden_fuentes = ["elpais", "20minutos", "newsapi", "newsdata"]
    fuentes_ordenadas = [f for f in orden_fuentes if f in por_fuente]
    fuentes_ordenadas += [f for f in por_fuente if f not in fuentes_ordenadas]

    idx_cat = 0 if idioma == "es" else 1

    for fuente in fuentes_ordenadas:
        noticias_fuente = por_fuente[fuente]
        nombre = _nombre_fuente(fuente)

        if idioma == "es":
            partes.append(f"Pasamos ahora a las noticias de {nombre}.")
        else:
            partes.append(f"Now, the news from {nombre}.")

        # Agrupar por categoría dentro de la fuente
        por_cat = {}
        for n in noticias_fuente:
            cat = n.get("categoria", "otros")
            por_cat.setdefault(cat, []).append(n)

        for categoria, nombres_cat in nombres_categoria.items():
            noticias_cat = por_cat.get(categoria, [])
            if not noticias_cat:
                continue

            cat_nombre = nombres_cat[idx_cat]
            if idioma == "es":
                partes.append(f"En {cat_nombre}.")
            else:
                partes.append(f"In {cat_nombre}.")

            total = len(noticias_cat)
            for i, n in enumerate(noticias_cat):
                if idioma == "es":
                    titulo = n.get("titulo_es") or n.get("titulo", "")
                else:
                    titulo = n.get("titulo", "")
                es_ultima = (i == total - 1) and (total > 1)
                transicion = _transicion(i, es_ultima)
                partes.append(f"{transicion}{titulo}.")

    # Cierre
    if idioma == "es":
        partes.append(
            "Esto ha sido el resumen de noticias del día. "
            "Gracias por escucharnos y hasta mañana."
        )
    else:
        partes.append(
            "That's all for today's news summary. "
            "Thank you for listening and see you tomorrow."
        )

    return " ".join(partes)


def generar_podcast_multifuente(
    noticias: list[dict],
    speech_key: str,
    speech_region: str,
    idioma: str = "es",
    carpeta_salida: str = "output",
) -> str:
    """
    Genera un podcast organizado por fuente.
    idioma="es" → voz española, idioma="en" → voz inglesa.
    Devuelve la ruta del fichero MP3.
    """
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d")
    fichero_salida = str(Path(carpeta_salida) / f"podcast_{idioma}_{fecha}.mp3")

    print(f"  → Construyendo texto del podcast ({idioma.upper()})...")
    texto = construir_texto_podcast_multifuente(noticias, idioma=idioma)
    print(f"  → Texto generado ({len(texto)} caracteres)")
    print("  → Convirtiendo a voz con Azure Speech...")

    # Elegir voz según idioma
    config_speech = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    if idioma == "en":
        config_speech.speech_synthesis_voice_name = "en-US-AvaMultilingualNeural"
    else:
        config_speech.speech_synthesis_voice_name = "es-MX-Ximena:DragonHDLatestNeural"

    config_speech.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )
    config_audio = speechsdk.audio.AudioOutputConfig(filename=fichero_salida)
    sintetizador = speechsdk.SpeechSynthesizer(
        speech_config=config_speech, audio_config=config_audio
    )

    resultado = sintetizador.speak_text_async(texto).get()

    if resultado.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"  ✓ Audio generado: {fichero_salida}")
        return fichero_salida
    elif resultado.reason == speechsdk.ResultReason.Canceled:
        detalles = speechsdk.CancellationDetails.from_result(resultado)
        raise RuntimeError(f"Error en Speech: {detalles.reason} — {detalles.error_details}")

    return fichero_salida


def previsualizar_texto_podcast(noticias_analizadas: list[dict]) -> str:
    """
    Devuelve el texto del podcast sin generar audio.
    Útil para revisar el contenido antes de consumir créditos de la API.
    """
    return construir_texto_podcast(noticias_analizadas)