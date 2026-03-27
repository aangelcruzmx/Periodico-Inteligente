# Periódico Inteligente con Azure AI

Aplicación de análisis automático de noticias que combina scraping web, APIs de noticias, procesamiento con Azure AI, clasificación documental y generación de podcasts con Streamlit como interfaz principal.

## Qué hace el proyecto

- Recopila noticias desde varias fuentes en una única edición diaria.
- Analiza cada noticia con Azure AI Language para detectar idioma, extraer frases clave y calcular sentimiento.
- Traduce automáticamente noticias en inglés al español con Azure Translator cuando la opción está activada.
- Clasifica los artículos en disco por categoría e idioma.
- Genera podcasts automáticos en español e inglés con Azure Speech.
- Muestra una interfaz Streamlit con filtros, métricas, análisis editorial y reproductor de audio.

## Fuentes de noticias soportadas

| Fuente | Tipo | Idioma habitual | Módulo |
|---|---|---|---|
| El País | Scraping web | Español | `src/scraper_elpais.py` |
| 20 Minutos | Scraping web | Español | `src/scraper_20minutos.py` |
| NewsData.io | API REST | Inglés | `src/api_newsdata.py` |
| NewsAPI.org | API REST | Español | `src/api_newsapi.py` |

El pipeline está diseñado para seguir funcionando aunque una fuente falle o falte una clave opcional. En esos casos registra avisos y continúa con el resto de orígenes disponibles.

## Servicios Azure utilizados

| Servicio | Uso dentro del proyecto |
|---|---|
| Azure AI Language | Detección de idioma, extracción de frases clave, análisis de sentimiento y apoyo a la categorización |
| Azure AI Translator | Traducción de noticias en inglés al español para homogeneizar la edición |
| Azure AI Speech | Síntesis de voz para generar podcasts en MP3 |
| Azure AI Vision | Soporte opcional y planteado como alternativa OCR si el scraping deja de estar disponible |

## Flujo del pipeline

El flujo principal está implementado en `src/pipeline.py` y ejecuta estos pasos:

1. Recopilación multi-fuente de noticias.
2. Guardado de la captura diaria en `data/noticias_hoy.json`.
3. Análisis con Azure Language.
4. Traducción opcional de noticias no españolas.
5. Guardado enriquecido en `data/noticias_analizadas.json`.
6. Clasificación automática en carpetas por categoría e idioma.
7. Generación opcional de podcasts en `output/`.

Las categorías reconocidas por el sistema son `politica`, `economia`, `deportes`, `tecnologia`, `cultura` y `otros`.

## Interfaz Streamlit

La aplicación principal se ejecuta desde `app.py` e incluye:

- Pestaña de edición diaria con ejecución del pipeline y seguimiento del estado.
- Configuración por fuente, número de noticias por fuente, traducción y generación de podcast.
- Filtros por categoría, idioma y fuente.
- Vista de noticias con tarjetas, etiquetas de categoría, sentimiento y enlace al artículo original.
- Panel analítico con métricas editoriales, distribución por categorías, sentimiento y fuentes.
- Reproductor integrado para los podcasts generados y vista previa del texto narrado.

## Estructura del proyecto

```text
periodico-inteligente/
├── app.py                           # Aplicación Streamlit principal
├── appProvisional.py                # Variante/prototipo adicional de la app
├── README.md
├── requirements.txt
├── notebooks/
│   └── periodico_inteligente.ipynb  # Recorrido paso a paso del proyecto
├── src/
│   ├── api_newsapi.py               # Cliente para NewsAPI
│   ├── api_newsdata.py              # Cliente para NewsData.io
│   ├── azure_language.py            # Integración con Azure AI Language
│   ├── azure_speech.py              # Generación de podcasts y texto narrado
│   ├── azure_translator.py          # Traducción con Azure Translator
│   ├── clasificador.py              # Clasificación y guardado por carpetas
│   ├── pipeline.py                  # Orquestación del flujo completo
│   ├── scraper_20minutos.py         # Scraping de 20 Minutos
│   └── scraper_elpais.py            # Scraping de El País
├── data/
│   ├── noticias_hoy.json            # Captura bruta de la edición
│   ├── noticias_analizadas.json     # Noticias enriquecidas con Azure AI
│   └── articulos/                   # Artículos clasificados por categoría/idioma
└── output/                          # Podcasts generados en MP3
```

## Requisitos

- Python 3.10 o superior.
- Una suscripción de Azure con acceso a Language y Speech.
- Claves de NewsAPI y NewsData si se quieren usar las fuentes externas por API.
- Jupyter Notebook opcional para ejecutar el cuaderno demostrativo.

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd periodico-inteligente
```

### 2. Crear un entorno virtual

PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS o Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear el archivo `.env`

Crea un archivo `.env` en la raíz del proyecto con las variables que correspondan a tu configuración:

```env
LANGUAGE_KEY=
LANGUAGE_ENDPOINT=

SPEECH_KEY=
SPEECH_REGION=

NEWSAPI_KEY=
NEWSDATA_KEY=

TRANSLATOR_KEY=
TRANSLATOR_REGION=
TRANSLATOR_ENDPOINT=

VISION_KEY=
VISION_ENDPOINT=
```

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `LANGUAGE_KEY` | Sí | Clave de Azure AI Language |
| `LANGUAGE_ENDPOINT` | Sí | Endpoint del recurso de Azure AI Language |
| `SPEECH_KEY` | Sí, si se genera audio | Clave de Azure Speech |
| `SPEECH_REGION` | Sí, si se genera audio | Región del recurso de Speech |
| `NEWSAPI_KEY` | No | Clave para consultar NewsAPI |
| `NEWSDATA_KEY` | No | Clave para consultar NewsData.io |
| `TRANSLATOR_KEY` | No | Clave de Azure Translator |
| `TRANSLATOR_REGION` | No | Región del recurso de Translator |
| `TRANSLATOR_ENDPOINT` | No | Endpoint de Azure Translator |
| `VISION_KEY` | No | Clave de Azure AI Vision |
| `VISION_ENDPOINT` | No | Endpoint de Azure AI Vision |

## Salidas generadas

Durante la ejecución se generan estos artefactos:

- `data/noticias_hoy.json`: noticias recopiladas antes del análisis.
- `data/noticias_analizadas.json`: noticias enriquecidas con idioma, frases clave, sentimiento y categoría.
- `data/articulos/<categoria>/<idioma>/*.json`: artículos clasificados y persistidos individualmente.
- `output/podcast_es_YYYY-MM-DD.mp3`: podcast en español.
- `output/podcast_en_YYYY-MM-DD.mp3`: podcast en inglés cuando hay noticias en ese idioma.

## Notebook del proyecto

El cuaderno `notebooks/periodico_inteligente.ipynb` documenta el proyecto paso a paso y sirve como apoyo docente para demostrar:

- scraping y recopilación de noticias,
- análisis con Azure Language,
- traducción con Azure Translator,
- clasificación en carpetas,
- generación de podcasts mono-fuente y multi-fuente.

## Uso recomendado

1. Inicia la app con Streamlit.
2. En la pestaña de edición, selecciona las fuentes que quieres consultar.
3. Decide si deseas traducir noticias en inglés y generar podcast.
4. Ejecuta el pipeline diario.
5. Revisa las pestañas de noticias, análisis y podcast para consumir la edición.

## Observaciones

- La traducción solo se aplica si existen noticias no españolas y las credenciales de Translator están configuradas.
- El podcast en inglés solo se genera si hay noticias con `codigo_idioma = en`.
- Azure Vision aparece como capacidad complementaria del proyecto, pero el flujo principal actual se apoya en scraping y APIs de noticias.
