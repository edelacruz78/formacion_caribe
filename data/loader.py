import pandas as pd
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@st.cache_data(show_spinner="Cargando datos de formación...")
def load_bd(path: str = None) -> pd.DataFrame:
    """Carga y normaliza la pestaña BD Consolidada."""
    if path is None:
        path = config.EXCEL_PATH

    df = pd.read_excel(path, sheet_name="BD Consolidada", engine="openpyxl")

    # Normalizar nombres de columnas (quitar espacios extra)
    df.columns = [c.strip() for c in df.columns]

    # Convertir Year a int y Total Hours a float
    df[config.BD["year"]] = pd.to_numeric(df[config.BD["year"]], errors="coerce").astype("Int64")
    df[config.BD["hours"]] = pd.to_numeric(df[config.BD["hours"]], errors="coerce").fillna(0.0)

    # Normalizar Level_norm: vacíos → "Sin Clasificar"
    df[config.BD["level"]] = df[config.BD["level"]].astype(str).str.strip()
    df[config.BD["level"]] = df[config.BD["level"]].replace({"nan": "Sin Clasificar", "": "Sin Clasificar"})

    # Normalizar strings en columnas de filtro
    for col in [config.BD["country"], config.BD["bu"], config.BD["school"],
                config.BD["type"], config.BD["gender"], config.BD["division"],
                config.BD["company"]]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Columna nombre completo para búsqueda
    df["Nombre Completo"] = (
        df[config.BD["first_name"]].fillna("").astype(str).str.strip()
        + " "
        + df[config.BD["last_name"]].fillna("").astype(str).str.strip()
    ).str.strip()

    return df


@st.cache_data(show_spinner="Cargando headcount...")
def load_hc(path: str = None) -> pd.DataFrame:
    """Carga y normaliza la pestaña HeadCount."""
    if path is None:
        path = config.EXCEL_PATH

    df = pd.read_excel(path, sheet_name="HeadCount", engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]

    # Solo empleados de planta (EMPLOYEE), excluye APPRENTICE y TEMPORARY
    # para que el denominador h/HC sea consistente con la metodología IIFTO
    df = df[df[config.HC["emp_group"]] == "EMPLOYEE"].copy()

    df[config.HC["year"]] = pd.to_numeric(df[config.HC["year"]], errors="coerce").astype("Int64")

    # Mapear código de país → nombre completo (igual que BD)
    df["Country"] = df[config.HC["country"]].map(config.HC_COUNTRY_MAP).fillna(df[config.HC["country"]])

    # Mapear JOB LEVEL → Level_norm
    df["Level_norm"] = df[config.HC["job_level"]].map(config.HC_LEVEL_MAP).fillna("Sin Clasificar")

    # Normalizar Business Unit (mayúsculas → title case para comparación)
    df["Business Unit"] = df[config.HC["bu"]].astype(str).str.strip().str.title()

    # Was_Trained como booleano
    df["Was_Trained_bool"] = df[config.HC["was_trained"]].astype(str).str.upper().str.strip() == "SI"

    return df


def apply_bd_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Aplica los filtros del sidebar a BD Consolidada.
    filters: dict con claves = columna, valor = lista de valores seleccionados.
    Lista vacía significa "sin filtro" (todos incluidos).
    """
    for col, values in filters.items():
        if values and col in df.columns:
            df = df[df[col].isin(values)]
    return df


def apply_hc_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Aplica solo los filtros relevantes para HeadCount.
    Excluye filtros de School, Type (Modalidad) y Progress State
    porque esas dimensiones no existen en HC.
    """
    HC_VALID_FILTERS = {
        config.BD["year"]: config.HC["year"],      # "Year" -> "AÑO"
        "Country": "Country",                       # ya mapeado en load_hc
        "Business Unit": "Business Unit",           # ya normalizado en load_hc
        config.BD["level"]: "Level_norm",           # "Level_norm"
    }

    for bd_col, hc_col in HC_VALID_FILTERS.items():
        values = filters.get(bd_col, [])
        if values and hc_col in df.columns:
            df = df[df[hc_col].isin(values)]

    return df
