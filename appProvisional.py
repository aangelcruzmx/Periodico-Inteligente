import json
import sys
import re
import html
from pathlib import Path
from datetime import datetime
from collections import Counter

import streamlit as st
from dotenv import load_dotenv

# ── Rutas ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.append(str(ROOT))

load_dotenv(ROOT / ".env")

NOTICIAS_JSON = ROOT / "data" / "noticias_analizadas.json"
CARPETA_OUTPUT = ROOT / "output"

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Periódico Inteligente",
    page_icon="📰",
    layout="wide",
)

# ── Estados de sesión ─────────────────────────────────────────────────────────
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False

if "pipeline_logs" not in st.session_state:
    st.session_state.pipeline_logs = []

if "pipeline_resultado" not in st.session_state:
    st.session_state.pipeline_resultado = None

if "pipeline_status" not in st.session_state:
    st.session_state.pipeline_status = None

# ── Estilos base ──────────────────────────────────────────────────────────────
COLORES_CATEGORIA = {
    "politica": "#E74C3C",
    "economia": "#2ECC71",
    "deportes": "#3498DB",
    "tecnologia": "#9B59B6",
    "cultura": "#F39C12",
    "otros": "#95A5A6",
}

ICONOS_CATEGORIA = {
    "politica": "🏛️",
    "economia": "📈",
    "deportes": "⚽",
    "tecnologia": "💻",
    "cultura": "🎭",
    "otros": "📌",
}

ICONOS_SENTIMIENTO = {
    "positive": "😊",
    "negative": "😟",
    "neutral": "😐",
    "mixed": "🤔",
}

NOMBRES_SENTIMIENTO = {
    "positive": "Positivo",
    "negative": "Negativo",
    "neutral": "Neutro",
    "mixed": "Mixto",
}

NOMBRES_FUENTE = {
    "elpais": "El País",
    "20minutos": "20 Minutos",
    "newsdata": "NewsData",
    "newsapi": "NewsAPI",
}

ICONOS_FUENTE = {
    "elpais": "🇪🇸",
    "20minutos": "📰",
    "newsdata": "🌍",
    "newsapi": "🔗",
}

st.markdown("""
<style>
    .titulo-app {
        font-size: 4rem !important;
        font-weight: 800 !important;
        margin-bottom: 0 !important;
        line-height: 1.05 !important;
        letter-spacing: -0.5px !important;
    }

    .subtitulo-app {
        color: #9aa4b2;
        font-size: 1.05rem;
        margin-top: 0.35rem;
        margin-bottom: 1.6rem;
    }

    .tarjeta-noticia {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 5px solid #ccc;
    }

    .badge-categoria {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
        margin-right: 6px;
    }

    .badge-sentimiento {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        background: #2a2a3e;
        color: #ccc;
    }

    .titulo-noticia {
        font-size: 1rem;
        font-weight: 600;
        margin: 0.5rem 0 0.2rem 0;
        color: #f0f0f0;
    }

    .resumen-noticia {
        font-size: 0.85rem;
        color: #aaa;
        margin: 0.25rem 0 0 0;
        line-height: 1.45;
    }

    .divider {
        border: none;
        border-top: 1px solid #2a2a3e;
        margin: 1.5rem 0;
    }

    .hero-box {
        background: linear-gradient(135deg, #131722 0%, #1a2130 100%);
        border: 1px solid #2a3242;
        border-radius: 18px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .hero-text {
        color: #b7c0cd;
        font-size: 0.95rem;
        margin-bottom: 0;
    }

    .metric-card {
        background: #151b26;
        border: 1px solid #2a3242;
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
    }

    .metric-label {
        color: #92a0b5;
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f2f5f8;
    }

    .section-card {
        background: #111723;
        border: 1px solid #283142;
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 1rem;
    }

    /* ── Tabs principales ───────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem !important;
        background: rgba(255, 255, 255, 0.08) !important;
        padding: 0.5rem !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 16px !important;
        margin-bottom: 1rem !important;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: auto !important;
        height: auto !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.10) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.14) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
    }

    .stTabs [data-baseweb="tab"] *,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #f3f6fa !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(126, 184, 218, 0.25) !important;
        border: 1px solid rgba(126, 184, 218, 0.45) !important;
        color: #ffffff !important;
        box-shadow: 0 0 0 1px rgba(126, 184, 218, 0.12) inset !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data
def cargar_noticias():
    if not NOTICIAS_JSON.exists():
        return []
    with open(NOTICIAS_JSON, encoding="utf-8") as f:
        return json.load(f)


def encontrar_podcast():
    if not CARPETA_OUTPUT.exists():
        return {}

    podcasts = {}
    for idioma in ("es", "en"):
        mp3s = sorted(CARPETA_OUTPUT.glob(f"podcast_{idioma}_*.mp3"), reverse=True)
        if mp3s:
            podcasts[idioma] = mp3s[0]

    if not podcasts:
        mp3s = sorted(CARPETA_OUTPUT.glob("podcast_*.mp3"), reverse=True)
        if mp3s:
            podcasts["es"] = mp3s[0]

    return podcasts


def obtener_fecha_ultima_actualizacion():
    if NOTICIAS_JSON.exists():
        ts = NOTICIAS_JSON.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
    return "Sin datos"


def construir_resumen_edicion(noticias: list[dict]):
    total = len(noticias)
    fuentes = sorted(set(n.get("fuente", "desconocida") for n in noticias)) if noticias else []
    idiomas = sorted(set(n.get("codigo_idioma", "es") for n in noticias)) if noticias else []
    podcasts = encontrar_podcast()

    return {
        "total_noticias": total,
        "total_fuentes": len(fuentes),
        "fuentes": fuentes,
        "idiomas": idiomas,
        "podcasts": podcasts,
        "ultima_actualizacion": obtener_fecha_ultima_actualizacion(),
    }


def limpiar_html_texto(texto: str) -> str:
    if not texto:
        return ""

    texto = html.unescape(texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def obtener_texto_noticia(n: dict) -> str:
    partes = [
        limpiar_html_texto(n.get("titulo", "")),
        limpiar_html_texto(n.get("titulo_es", "")),
        limpiar_html_texto(n.get("resumen", "")),
    ]
    return " ".join(p for p in partes if p).strip()


def obtener_palabras_y_bigramas(noticias: list[dict], top_n: int = 10):
    stopwords = {
        "de", "la", "el", "los", "las", "y", "en", "a", "del", "que", "un", "una",
        "por", "con", "para", "al", "se", "su", "sus", "es", "como", "más", "mas",
        "ya", "ha", "han", "fue", "ser", "sin", "sobre", "entre", "tras", "desde",
        "hasta", "también", "tambien", "pero", "este", "esta", "estos", "estas",
        "eso", "esa", "esos", "esas", "hoy", "ayer", "ante", "contra", "durante",
        "muy", "todo", "toda", "todos", "todas", "uno", "dos", "tres", "e", "o",
        "u", "le", "les", "lo", "ya", "cada", "donde", "qué", "que", "cuando",
        "quien", "quienes", "cual", "cuales", "aunque", "porque", "según", "segun"
    }

    palabras = []
    bigramas = []

    for noticia in noticias:
        texto = obtener_texto_noticia(noticia).lower()
        texto = re.sub(r"[^a-záéíóúñü\s]", " ", texto)
        tokens = [t for t in texto.split() if len(t) > 2 and t not in stopwords]

        palabras.extend(tokens)

        for i in range(len(tokens) - 1):
            bigrama = f"{tokens[i]} {tokens[i+1]}"
            bigramas.append(bigrama)

    conteo_palabras = Counter(palabras).most_common(top_n)
    conteo_bigramas = Counter(bigramas).most_common(top_n)

    return conteo_palabras, conteo_bigramas




def fecha_actual_es():
    dias = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }

    meses = {
        "January": "enero",
        "February": "febrero",
        "March": "marzo",
        "April": "abril",
        "May": "mayo",
        "June": "junio",
        "July": "julio",
        "August": "agosto",
        "September": "septiembre",
        "October": "octubre",
        "November": "noviembre",
        "December": "diciembre",
    }

    ahora = datetime.now()
    dia = dias[ahora.strftime("%A")]
    mes = meses[ahora.strftime("%B")]
    return f"{dia} {ahora.day} de {mes} de {ahora.year}"


def tarjeta_noticia(n: dict):
    cat = n.get("categoria", "otros")
    color = COLORES_CATEGORIA.get(cat, "#95A5A6")
    icono_cat = ICONOS_CATEGORIA.get(cat, "📌")

    sent = n.get("sentimiento", "neutral")
    icono_sent = ICONOS_SENTIMIENTO.get(sent, "😐")
    nombre_sent = NOMBRES_SENTIMIENTO.get(sent, sent)

    titulo = limpiar_html_texto(n.get("titulo", "Sin título"))
    titulo_es = limpiar_html_texto(n.get("titulo_es", ""))
    resumen = limpiar_html_texto(n.get("resumen", ""))
    resumen_corto = resumen[:160] + "..." if len(resumen) > 160 else resumen

    url = n.get("url", "#")
    fuente = n.get("fuente", "")
    nombre_fuente = NOMBRES_FUENTE.get(fuente, fuente)
    icono_fuente = ICONOS_FUENTE.get(fuente, "📰")

    badge_fuente = (
        f'<span class="badge-sentimiento">{icono_fuente} {nombre_fuente}</span>'
        if fuente else ""
    )

    bloque_titulo_es = f'<p class="resumen-noticia" style="color:#7eb8da; font-style:italic;">🌐 {titulo_es}</p>' if titulo_es else ''
    bloque_resumen = f'<p class="resumen-noticia">{resumen_corto}</p>' if resumen else ''

    st.markdown(
        f'<div class="tarjeta-noticia" style="border-left-color: {color};">'
        f'<span class="badge-categoria" style="background:{color};">{icono_cat} {cat.upper()}</span>'
        f'<span class="badge-sentimiento">{icono_sent} {nombre_sent}</span>'
        f'{badge_fuente}'
        f'<p class="titulo-noticia">{titulo}</p>'
        f'{bloque_titulo_es}'
        f'{bloque_resumen}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(f"[🔗 Leer artículo completo]({url})", unsafe_allow_html=False)


def grafica_sentimientos(noticias: list[dict]):
    conteo = {"Positivo": 0, "Negativo": 0, "Neutro": 0, "Mixto": 0}
    mapa = {
        "positive": "Positivo",
        "negative": "Negativo",
        "neutral": "Neutro",
        "mixed": "Mixto",
    }

    for n in noticias:
        clave = mapa.get(n.get("sentimiento", "neutral"), "Neutro")
        conteo[clave] += 1

    import pandas as pd

    df = pd.DataFrame({
        "Sentimiento": list(conteo.keys()),
        "Noticias": list(conteo.values()),
    })
    df = df[df["Noticias"] > 0]

    if df.empty:
        st.info("No hay datos suficientes para mostrar sentimientos.")
        return

    st.bar_chart(df.set_index("Sentimiento")["Noticias"])


def ejecutar_pipeline_ui(generar_audio, traducir, max_noticias, fuentes_config):
    from src.pipeline import ejecutar_pipeline

    st.session_state.pipeline_running = True
    st.session_state.pipeline_logs = []
    st.session_state.pipeline_resultado = None
    st.session_state.pipeline_status = "Iniciando proceso..."

    progreso = st.empty()
    barra = st.progress(0)
    log_box = st.container()

    mapa_progreso = {
        "scraping": 20,
        "analisis": 40,
        "traduccion": 60,
        "clasificacion": 80,
        "podcast": 90,
        "completado": 100,
    }

    try:
        for paso, mensaje in ejecutar_pipeline(
            generar_audio=generar_audio,
            traducir=traducir,
            max_noticias=max_noticias,
            fuentes=fuentes_config,
        ):
            st.session_state.pipeline_status = mensaje

            if paso == "aviso":
                st.session_state.pipeline_logs.append(("warning", mensaje))
            elif paso == "completado":
                st.session_state.pipeline_resultado = mensaje
                progreso.success("✅ Edición generada correctamente")
                barra.progress(100)
            else:
                porcentaje = mapa_progreso.get(paso, 10)
                barra.progress(porcentaje)
                progreso.info(f"⏳ {mensaje}")
                st.session_state.pipeline_logs.append(("info", mensaje))

            with log_box:
                for tipo, texto in st.session_state.pipeline_logs:
                    if tipo == "warning":
                        st.warning(texto)
                    else:
                        st.info(texto)

        st.cache_data.clear()
        st.session_state.pipeline_running = False
        st.balloons()
        st.rerun()

    except Exception as e:
        st.session_state.pipeline_running = False
        progreso.error(f"❌ Error durante la generación: {e}")
        with log_box:
            for tipo, texto in st.session_state.pipeline_logs:
                if tipo == "warning":
                    st.warning(texto)
                else:
                    st.info(texto)


# ── Layout principal ──────────────────────────────────────────────────────────
st.markdown('<p class="titulo-app">📰 Periódico Inteligente</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="subtitulo-app">Multi-fuente · Análisis con Azure AI · {fecha_actual_es()}</p>',
    unsafe_allow_html=True
)

noticias = cargar_noticias()
resumen_edicion = construir_resumen_edicion(noticias)
hay_datos = len(noticias) > 0

# ── Sidebar — Filtros ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Filtros")

    if hay_datos:
        categorias_disponibles = sorted(set(n.get("categoria", "otros") for n in noticias))
        opciones_cat = ["Todas"] + [
            f"{ICONOS_CATEGORIA.get(c, '📌')} {c.capitalize()}"
            for c in categorias_disponibles
        ]
        filtro_cat = st.selectbox("Categoría", opciones_cat)

        idiomas_disponibles = sorted(set(n.get("codigo_idioma", "es") for n in noticias))
        opciones_idioma = ["Todos"] + idiomas_disponibles
        filtro_idioma = st.selectbox("Idioma", opciones_idioma)

        fuentes_disponibles = sorted(set(n.get("fuente", "elpais") for n in noticias))
        opciones_fuente = ["Todas"] + [
            f"{ICONOS_FUENTE.get(f, '📰')} {NOMBRES_FUENTE.get(f, f)}"
            for f in fuentes_disponibles
        ]
        filtro_fuente = st.selectbox("Fuente", opciones_fuente)

        st.markdown("---")
        st.subheader("📊 Resumen")
        st.caption(f"{len(noticias)} noticias cargadas")

        conteo_fuentes = Counter(n.get("fuente", "elpais") for n in noticias)
        for fuente, cantidad in conteo_fuentes.most_common():
            icono = ICONOS_FUENTE.get(fuente, "📰")
            nombre = NOMBRES_FUENTE.get(fuente, fuente)
            st.caption(f"{icono} {nombre}: {cantidad}")
    else:
        filtro_cat = "Todas"
        filtro_idioma = "Todos"
        filtro_fuente = "Todas"
        st.info("Aún no hay edición cargada. Usa la pestaña 'Edición de hoy'.")

    st.markdown("---")
    if st.button("🔄 Recargar noticias"):
        st.cache_data.clear()
        st.rerun()

# ── Aplicar filtros ───────────────────────────────────────────────────────────
noticias_filtradas = noticias

if hay_datos:
    if filtro_cat != "Todas":
        cat_limpia = filtro_cat.split(" ", 1)[1].lower()
        noticias_filtradas = [n for n in noticias_filtradas if n.get("categoria") == cat_limpia]

    if filtro_idioma != "Todos":
        noticias_filtradas = [n for n in noticias_filtradas if n.get("codigo_idioma") == filtro_idioma]

    if filtro_fuente != "Todas":
        fuente_limpia = filtro_fuente.split(" ", 1)[1]
        fuente_clave = next(
            (k for k, v in NOMBRES_FUENTE.items() if v == fuente_limpia),
            fuente_limpia
        )
        noticias_filtradas = [n for n in noticias_filtradas if n.get("fuente") == fuente_clave]

# ── Tabs principales ──────────────────────────────────────────────────────────
tab_edicion, tab_noticias, tab_grafica, tab_podcast = st.tabs([
    "🗞️ Edición de hoy",
    "📋 Noticias",
    "📊 Análisis",
    "🎙️ Podcast",
])

# ── Tab 1: Edición de hoy ─────────────────────────────────────────────────────
with tab_edicion:
    if hay_datos:
        st.markdown("""
        <div class="hero-box">
            <div class="hero-title">Edición disponible</div>
            <p class="hero-text">
                Ya existe una edición generada. Puedes consultarla en las demás pestañas
                o volver a actualizarla desde aquí.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="hero-box">
            <div class="hero-title">Aún no hay edición disponible</div>
            <p class="hero-text">
                Genera la edición del día para recopilar noticias, analizarlas,
                clasificarlas y preparar el podcast automáticamente.
            </p>
        </div>
        """, unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Noticias</div><div class="metric-value">{resumen_edicion["total_noticias"]}</div></div>',
            unsafe_allow_html=True
        )
    with col_m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Fuentes</div><div class="metric-value">{resumen_edicion["total_fuentes"]}</div></div>',
            unsafe_allow_html=True
        )
    with col_m3:
        idiomas_txt = ", ".join(i.upper() for i in resumen_edicion["idiomas"]) if resumen_edicion["idiomas"] else "—"
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Idiomas</div><div class="metric-value">{idiomas_txt}</div></div>',
            unsafe_allow_html=True
        )
    with col_m4:
        podcast_txt = "Sí" if resumen_edicion["podcasts"] else "No"
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Podcast</div><div class="metric-value">{podcast_txt}</div></div>',
            unsafe_allow_html=True
        )

    st.caption(f"Última actualización: {resumen_edicion['ultima_actualizacion']}")
    st.markdown("---")

    col_cfg, col_estado = st.columns([1.25, 1])

    with col_cfg:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("⚙️ Configuración")

        opt_audio = st.checkbox(
            "Generar podcast",
            value=True,
            disabled=st.session_state.pipeline_running,
        )
        opt_traducir = st.checkbox(
            "Traducir noticias (EN→ES)",
            value=True,
            disabled=st.session_state.pipeline_running,
        )
        opt_max = st.slider(
            "Noticias por fuente",
            min_value=1,
            max_value=20,
            value=10,
            disabled=st.session_state.pipeline_running,
        )

        st.markdown("**Fuentes a consultar**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            src_elpais = st.checkbox(
                "🇪🇸 El País",
                value=True,
                disabled=st.session_state.pipeline_running,
            )
            src_20min = st.checkbox(
                "📰 20 Minutos",
                value=True,
                disabled=st.session_state.pipeline_running,
            )
        with col_f2:
            src_newsdata = st.checkbox(
                "🌍 NewsData",
                value=True,
                disabled=st.session_state.pipeline_running,
            )
            src_newsapi = st.checkbox(
                "🔗 NewsAPI",
                value=True,
                disabled=st.session_state.pipeline_running,
            )

        fuentes_config = {
            "elpais": src_elpais,
            "20minutos": src_20min,
            "newsdata": src_newsdata,
            "newsapi": src_newsapi,
        }

        boton_label = "⏳ Procesando edición..." if st.session_state.pipeline_running else (
            "🔄 Actualizar edición" if hay_datos else "🚀 Generar edición de hoy"
        )

        ejecutar = st.button(
            boton_label,
            type="primary",
            disabled=st.session_state.pipeline_running,
            use_container_width=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)

        if ejecutar:
            if not any(fuentes_config.values()):
                st.error("Debes seleccionar al menos una fuente.")
            else:
                ejecutar_pipeline_ui(
                    generar_audio=opt_audio,
                    traducir=opt_traducir,
                    max_noticias=opt_max,
                    fuentes_config=fuentes_config,
                )

    with col_estado:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📡 Estado de la edición")

        if st.session_state.pipeline_running:
            st.info(st.session_state.pipeline_status or "Procesando...")
            st.caption("El botón y las opciones están bloqueados hasta terminar.")
        else:
            if hay_datos:
                st.success("La edición actual está disponible para consulta.")
            else:
                st.warning("Todavía no se ha generado ninguna edición.")

        fuentes_legibles = [
            f"{ICONOS_FUENTE.get(f, '📰')} {NOMBRES_FUENTE.get(f, f)}"
            for f in resumen_edicion["fuentes"]
        ]
        st.markdown("**Fuentes presentes en la edición actual:**")
        if fuentes_legibles:
            for fuente in fuentes_legibles:
                st.write(f"- {fuente}")
        else:
            st.write("- Aún no hay fuentes cargadas")

        if st.session_state.pipeline_resultado:
            st.markdown("---")
            st.markdown("**Último resultado**")
            st.json(st.session_state.pipeline_resultado)

        st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 2: Noticias ───────────────────────────────────────────────────────────
with tab_noticias:
    if not hay_datos:
        st.info("Aún no hay noticias disponibles. Genera primero la edición del día.")
    else:
        st.markdown(f"**{len(noticias_filtradas)} noticias** encontradas")
        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        if not noticias_filtradas:
            st.info("No hay noticias con los filtros seleccionados.")
        else:
            for n in noticias_filtradas:
                tarjeta_noticia(n)

# ── Tab 3: Análisis ───────────────────────────────────────────────────────────
with tab_grafica:
    if not hay_datos:
        st.info("Aún no hay datos para analizar. Genera primero la edición del día.")
    else:
        import pandas as pd

        datos_graf = noticias_filtradas if noticias_filtradas else noticias

        if not datos_graf:
            st.info("No hay datos disponibles para el análisis.")
        else:
            # ── Preparación de datos ───────────────────────────────────────────
            total_noticias = len(datos_graf)

            conteo_sent = Counter(
                NOMBRES_SENTIMIENTO.get(n.get("sentimiento", "neutral"), "Neutro")
                for n in datos_graf
            )

            conteo_cat = Counter(
                n.get("categoria", "otros").capitalize()
                for n in datos_graf
            )

            conteo_fuente = Counter(
                NOMBRES_FUENTE.get(n.get("fuente", "desconocida"), n.get("fuente", "desconocida"))
                for n in datos_graf
            )

            sentimiento_dominante = conteo_sent.most_common(1)[0][0] if conteo_sent else "—"
            categoria_principal = conteo_cat.most_common(1)[0][0] if conteo_cat else "—"
            fuente_lider = conteo_fuente.most_common(1)[0][0] if conteo_fuente else "—"

            porcentaje_dominante = 0
            if conteo_sent and total_noticias > 0:
                porcentaje_dominante = round((conteo_sent.most_common(1)[0][1] / total_noticias) * 100)

            # ── Cabecera ejecutiva ─────────────────────────────────────────────
            st.markdown("""
            <div class="hero-box">
                <div class="hero-title">Resumen analítico del día</div>
                <p class="hero-text">
                    Una lectura rápida del comportamiento editorial de la edición actual:
                    tono predominante, temas más presentes y reparto por fuente.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

            with col_kpi1:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Noticias analizadas</div><div class="metric-value">{total_noticias}</div></div>',
                    unsafe_allow_html=True
                )

            with col_kpi2:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Sentimiento dominante</div><div class="metric-value">{sentimiento_dominante}</div></div>',
                    unsafe_allow_html=True
                )

            with col_kpi3:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Categoría principal</div><div class="metric-value">{categoria_principal}</div></div>',
                    unsafe_allow_html=True
                )

            with col_kpi4:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Fuente líder</div><div class="metric-value">{fuente_lider}</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown("")

            # ── Insight automático ─────────────────────────────────────────────
            top_3_categorias = conteo_cat.most_common(3)
            texto_top_categorias = ", ".join(
                f"{cat} ({cant})" for cat, cant in top_3_categorias
            ) if top_3_categorias else "sin categorías destacadas"

            equilibrio_fuentes = len(set(conteo_fuente.values())) == 1 if conteo_fuente else False
            texto_equilibrio = (
                "La distribución por fuente está bastante equilibrada."
                if equilibrio_fuentes else
                "La distribución por fuente muestra diferencias visibles entre proveedores."
            )

            st.markdown(
                f"""
                <div class="section-card">
                    <h4 style="margin-top:0; margin-bottom:0.6rem;">🧠 Lectura rápida del día</h4>
                    <p style="margin:0; color:#c7d0dd; line-height:1.6;">
                        En la edición actual predominan las noticias con tono
                        <strong>{sentimiento_dominante.lower()}</strong>, que representan aproximadamente
                        <strong>{porcentaje_dominante}%</strong> del total analizado.
                        La cobertura se concentra principalmente en
                        <strong>{texto_top_categorias}</strong>.
                        {texto_equilibrio}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ── DataFrames para visuales ───────────────────────────────────────
            df_sent = pd.DataFrame(
                {
                    "Sentimiento": list(conteo_sent.keys()),
                    "Noticias": list(conteo_sent.values()),
                }
            )

            df_cat = pd.DataFrame(
                {
                    "Categoría": list(conteo_cat.keys()),
                    "Noticias": list(conteo_cat.values()),
                }
            ).sort_values("Noticias", ascending=False)

            df_fuente = pd.DataFrame(
                {
                    "Fuente": list(conteo_fuente.keys()),
                    "Noticias": list(conteo_fuente.values()),
                }
            ).sort_values("Noticias", ascending=False)

            # ── Visuales principales ───────────────────────────────────────────
            fila_1_col_1, fila_1_col_2 = st.columns([1, 1.2])

            with fila_1_col_1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("📈 Sentimiento editorial")

                if not df_sent.empty:
                    st.bar_chart(df_sent.set_index("Sentimiento")["Noticias"])

                    sentimiento_detalle = [
                        f"{fila['Sentimiento']}: {fila['Noticias']} ({round((fila['Noticias']/total_noticias)*100)}%)"
                        for _, fila in df_sent.iterrows()
                    ]
                    st.caption(" · ".join(sentimiento_detalle))
                else:
                    st.info("No hay información de sentimientos para mostrar.")

                st.markdown('</div>', unsafe_allow_html=True)

            with fila_1_col_2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("🗂️ Distribución temática")

                if not df_cat.empty:
                    st.bar_chart(df_cat.set_index("Categoría")["Noticias"])
                    st.caption(
                        "Las categorías muestran qué temas concentraron mayor volumen en la edición actual."
                    )
                else:
                    st.info("No hay categorías disponibles para mostrar.")

                st.markdown('</div>', unsafe_allow_html=True)

            fila_2_col_1, fila_2_col_2 = st.columns([1, 1])

            with fila_2_col_1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("📰 Participación por fuente")

                if not df_fuente.empty:
                    st.bar_chart(df_fuente.set_index("Fuente")["Noticias"])

                    fuente_detalle = [
                        f"{fila['Fuente']}: {fila['Noticias']} ({round((fila['Noticias']/total_noticias)*100)}%)"
                        for _, fila in df_fuente.iterrows()
                    ]
                    st.caption(" · ".join(fuente_detalle))
                else:
                    st.info("No hay fuentes disponibles para mostrar.")

                st.markdown('</div>', unsafe_allow_html=True)

            with fila_2_col_2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("🏆 Top categorías del día")

                if not df_cat.empty:
                    top_df = df_cat.copy()
                    top_df["% del total"] = top_df["Noticias"].apply(
                        lambda x: f"{round((x / total_noticias) * 100)}%"
                    )
                    st.dataframe(
                        top_df.reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No hay categorías para resumir.")

                st.markdown('</div>', unsafe_allow_html=True)

            # ── Conclusión final ────────────────────────────────────────────────
            st.markdown(
                f"""
                <div class="hero-box" style="margin-top: 0.8rem;">
                    <div class="hero-title">Conclusión del análisis</div>
                    <p class="hero-text">
                        La edición actual presenta un predominio de contenido
                        <strong>{sentimiento_dominante.lower()}</strong>, con mayor presencia de la categoría
                        <strong>{categoria_principal.lower()}</strong>. La fuente más activa en esta selección es
                        <strong>{fuente_lider}</strong>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

# ── Tab 4: Podcast ────────────────────────────────────────────────────────────
with tab_podcast:
    if not hay_datos:
        st.info("Aún no hay edición cargada. Genera primero la edición del día.")
    else:
        st.subheader("🎙️ Podcast del día")

        podcasts = encontrar_podcast()

        if podcasts:
            nombres_idioma = {"es": "Español", "en": "English"}
            for idioma, ruta in podcasts.items():
                nombre = nombres_idioma.get(idioma, idioma.upper())
                st.success(f"Podcast {nombre}: `{ruta.name}`")
                with open(ruta, "rb") as f:
                    audio_bytes = f.read()

                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label=f"⬇️ Descargar MP3 ({nombre})",
                    data=audio_bytes,
                    file_name=ruta.name,
                    mime="audio/mp3",
                    key=f"download_{idioma}",
                )
                st.markdown("")
        else:
            st.info(
                "No se encontró ningún podcast para la edición actual. "
                "Puedes regenerar la edición activando la opción de audio."
            )

        st.markdown("---")
        st.subheader("📝 Texto del podcast")

        from src.azure_speech import construir_texto_podcast_multifuente

        tab_texto_es, tab_texto_en = st.tabs(["🇪🇸 Español", "🇬🇧 English"])

        with tab_texto_es:
            texto_es = construir_texto_podcast_multifuente(noticias, idioma="es")
            st.text_area("Texto narrado (ES)", value=texto_es, height=300, disabled=True)

        with tab_texto_en:
            texto_en = construir_texto_podcast_multifuente(noticias, idioma="en")
            st.text_area("Texto narrado (EN)", value=texto_en, height=300, disabled=True)