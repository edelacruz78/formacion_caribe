import streamlit as st
import sys
import os

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data.loader import load_bd, load_hc, apply_bd_filters, apply_hc_filters
from views import resumen_global, por_pais, por_nivel, por_escuela, por_colaborador

# ─── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Formación | Caribe 2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos personalizados
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700; }
    [data-testid="stMetricDelta"] { font-size: 0.9rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #E87722; color: #E87722; }
    h2, h3 { color: #004B87; }
    .stDataFrame { font-size: 0.88rem; }
</style>
""", unsafe_allow_html=True)

# ─── Carga de datos ────────────────────────────────────────────────────────────
bd = load_bd(config.EXCEL_PATH)
hc = load_hc(config.EXCEL_PATH)

# ─── Sidebar — Filtros ─────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Argos_SA_Logo.svg/200px-Argos_SA_Logo.svg.png",
        width=120,
    ) if False else None  # Logo opcional; descomenta si tienes el archivo local

    st.title("📊 Formación Caribe")
    st.caption("Dashboard IIFTO — Indicador de Intensidad de Formación Técnico-Operativa")
    st.divider()

    st.subheader("Filtros")

    # ── Año ────────────────────────────────────────────────────────────────────
    years_available = sorted(bd[config.BD["year"]].dropna().unique().tolist())
    selected_years = st.multiselect(
        "Año",
        options=years_available,
        default=years_available,
        key="filter_year",
    )

    # ── País ───────────────────────────────────────────────────────────────────
    countries = sorted(bd[config.BD["country"]].dropna().unique().tolist())
    selected_countries = st.multiselect(
        "País / Operación",
        options=countries,
        default=[],
        placeholder="Todos los países",
        key="filter_country",
    )

    # ── Unidad de Negocio ──────────────────────────────────────────────────────
    bus = sorted(bd[config.BD["bu"]].dropna().unique().tolist())
    selected_bu = st.multiselect(
        "Unidad de Negocio",
        options=bus,
        default=[],
        placeholder="Todas",
        key="filter_bu",
    )

    # ── Nivel Jerárquico ───────────────────────────────────────────────────────
    levels = [l for l in config.LEVEL_ORDER if l in bd[config.BD["level"]].unique()]
    selected_levels = st.multiselect(
        "Nivel Jerárquico",
        options=levels,
        default=[],
        placeholder="Todos los niveles",
        key="filter_level",
    )

    # ── Escuela / Área ─────────────────────────────────────────────────────────
    schools = [s for s in config.SCHOOL_ORDER if s in bd[config.BD["school"]].unique()]
    schools += [s for s in sorted(bd[config.BD["school"]].dropna().unique()) if s not in schools]
    selected_schools = st.multiselect(
        "Escuela / Área",
        options=schools,
        default=[],
        placeholder="Todas las escuelas",
        key="filter_school",
    )

    # ── Modalidad ──────────────────────────────────────────────────────────────
    modalities = sorted(bd[config.BD["type"]].dropna().unique().tolist())
    selected_modalities = st.multiselect(
        "Modalidad",
        options=modalities,
        default=[],
        placeholder="Presencial y virtual",
        key="filter_modality",
    )

    # ── Género (opcional) ──────────────────────────────────────────────────────
    with st.expander("Más filtros"):
        genders = sorted(bd[config.BD["gender"]].dropna().unique().tolist())
        selected_genders = st.multiselect(
            "Género",
            options=genders,
            default=[],
            placeholder="Todos",
            key="filter_gender",
        )
        divisions = sorted(bd[config.BD["division"]].dropna().unique().tolist())
        selected_divisions = st.multiselect(
            "División",
            options=divisions,
            default=[],
            placeholder="Todas",
            key="filter_division",
        )

    st.divider()

    # Conteo rápido de registros activos
    total_records = len(bd)
    st.caption(f"Base: {total_records:,} registros totales")

# ─── Construir diccionario de filtros ─────────────────────────────────────────
filters = {}
if selected_years:
    filters[config.BD["year"]] = selected_years
if selected_countries:
    filters[config.BD["country"]] = selected_countries
    filters["Country"] = selected_countries  # para HC (columna mapeada)
if selected_bu:
    filters[config.BD["bu"]] = selected_bu
    filters["Business Unit"] = [s.title() for s in selected_bu]  # HC usa title case
if selected_levels:
    filters[config.BD["level"]] = selected_levels
if selected_schools:
    filters[config.BD["school"]] = selected_schools
if selected_modalities:
    filters[config.BD["type"]] = selected_modalities
if selected_genders:
    filters[config.BD["gender"]] = selected_genders
if selected_divisions:
    filters[config.BD["division"]] = selected_divisions

# ─── Aplicar filtros ───────────────────────────────────────────────────────────
bd_f = apply_bd_filters(bd.copy(), filters)
hc_f = apply_hc_filters(hc.copy(), filters)

# ─── Header principal ──────────────────────────────────────────────────────────
st.markdown("# Dashboard de Formación — Argos Caribe")
col_hdr1, col_hdr2 = st.columns([3, 1])
with col_hdr1:
    active_filters = [k for k, v in filters.items() if v and k not in ["Country", "Business Unit"]]
    if active_filters:
        filter_labels = []
        if selected_countries:
            filter_labels.append(f"País: {', '.join(selected_countries)}")
        if selected_years and set(selected_years) != set(years_available):
            filter_labels.append(f"Año: {', '.join(str(y) for y in selected_years)}")
        if selected_levels:
            filter_labels.append(f"Nivel: {', '.join(selected_levels)}")
        if selected_schools:
            filter_labels.append(f"Escuela: {', '.join(selected_schools)}")
        if filter_labels:
            st.caption("Filtros activos: " + " | ".join(filter_labels))
    else:
        st.caption("Mostrando todos los datos (sin filtros activos)")

with col_hdr2:
    n_records = len(bd_f)
    n_persons = bd_f[config.BD["person_id"]].nunique() if n_records > 0 else 0
    st.caption(f"**{n_records:,}** registros | **{n_persons:,}** colaboradores")

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📋 Resumen Global",
    "🌍 Por País",
    "📊 Por Nivel",
    "🎓 Por Escuela",
    "👤 Por Colaborador",
])

with tabs[0]:
    resumen_global.render(bd_f, hc_f, bd, hc)

with tabs[1]:
    por_pais.render(bd_f, hc_f)

with tabs[2]:
    por_nivel.render(bd_f, hc_f)

with tabs[3]:
    por_escuela.render(bd_f, hc_f)

with tabs[4]:
    por_colaborador.render(bd_f)
