"""
Todas las fórmulas de métricas de formación.
Funciones puras: reciben DataFrames, retornan DataFrames o escalares.
Sin llamadas a Streamlit.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ─── Utilidades ──────────────────────────────────────────────────────────────

def safe_div(numerator: float, denominator: float) -> float:
    """División segura: retorna 0.0 cuando denominador es 0 o NaN."""
    if denominator == 0 or pd.isna(denominator) or numerator == 0:
        return 0.0
    return round(float(numerator) / float(denominator), 2)


def var_pct(val_new, val_old) -> float | None:
    """Variación porcentual. Retorna None si base es 0 o NaN (se muestra como N/A)."""
    if val_old is None or val_old == 0 or pd.isna(val_old):
        return None
    return (float(val_new) - float(val_old)) / float(val_old)


def fmt_var(v) -> str:
    """Formatea variación porcentual para mostrar en tablas."""
    if v is None or pd.isna(v):
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1%}"


# ─── Métricas de resumen ──────────────────────────────────────────────────────

def compute_summary(bd: pd.DataFrame, hc: pd.DataFrame) -> dict:
    """
    Retorna dict con todas las KPIs para un estado de filtro dado.
    bd: BD Consolidada ya filtrada
    hc: HeadCount ya filtrado (mismo alcance geográfico/organizacional)
    """
    participantes = int(bd[config.BD["person_id"]].nunique())
    total_horas = float(bd[config.BD["hours"]].sum())
    hc_total = int(len(hc))

    return {
        "participantes": participantes,
        "total_horas": round(total_horas, 2),
        "h_p_entrenados": safe_div(total_horas, participantes),
        "h_hc_total": safe_div(total_horas, hc_total),
        "sin_formacion": max(0, hc_total - participantes),
        "hc_total": hc_total,
    }


def compute_yoy_summary(bd: pd.DataFrame, hc: pd.DataFrame, years=(2024, 2025)) -> pd.DataFrame:
    """
    Tabla comparativa interanual de métricas globales.
    Retorna DataFrame con columnas: Métrica, 2024, 2025, Var%
    """
    rows = []
    year_col = config.BD["year"]
    hc_year_col = config.HC["year"]

    results = {}
    for y in years:
        bd_y = bd[bd[year_col] == y]
        hc_y = hc[hc[hc_year_col] == y]
        results[y] = compute_summary(bd_y, hc_y)

    def _row(label, key):
        v2024 = results.get(2024, {}).get(key, 0)
        v2025 = results.get(2025, {}).get(key, 0)
        return {
            "Métrica": label,
            "2024": v2024,
            "2025": v2025,
            "Var %": var_pct(v2025, v2024),
        }

    rows = [
        _row("Participantes con formación", "participantes"),
        _row("Total horas de formación", "total_horas"),
        _row("h/persona entrenado", "h_p_entrenados"),
        _row("h/HC total activo", "h_hc_total"),
        _row("Colaboradores sin formación", "sin_formacion"),
        _row("HC Total", "hc_total"),
    ]
    return pd.DataFrame(rows)


# ─── Por dimensión (país, nivel, escuela, etc.) ───────────────────────────────

def compute_by_dimension(
    bd: pd.DataFrame,
    hc: pd.DataFrame,
    bd_dim: str,
    hc_dim: str,
    years=(2024, 2025),
) -> pd.DataFrame:
    """
    Agrega métricas de formación por una dimensión para los años dados,
    luego combina en una tabla comparativa interanual.

    bd_dim: columna en BD (ej. "Country", "Level_norm")
    hc_dim: columna equivalente en HC (ej. "Country", "Level_norm")
    """
    year_col = config.BD["year"]
    hc_year_col = config.HC["year"]
    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]

    frames = {}
    for y in years:
        bd_y = bd[bd[year_col] == y]
        hc_y = hc[hc[hc_year_col] == y]

        # Participantes y horas desde BD
        grp = (
            bd_y.groupby(bd_dim, observed=True)
            .agg(
                Participantes=(pid_col, "nunique"),
                Total_Horas=(hrs_col, "sum"),
            )
            .reset_index()
        )

        # HC total desde HeadCount
        if hc_dim in hc_y.columns:
            hc_grp = hc_y.groupby(hc_dim, observed=True).size().reset_index(name="HC_Total")
            hc_grp = hc_grp.rename(columns={hc_dim: bd_dim})
            grp = grp.merge(hc_grp, on=bd_dim, how="left")
            grp["HC_Total"] = grp["HC_Total"].fillna(0).astype(int)
        else:
            grp["HC_Total"] = 0

        grp["h_p"] = grp.apply(
            lambda r: safe_div(r["Total_Horas"], r["Participantes"]), axis=1
        )
        grp["h_hc"] = grp.apply(
            lambda r: safe_div(r["Total_Horas"], r["HC_Total"]), axis=1
        )
        grp["Year"] = y
        frames[y] = grp

    if not frames:
        return pd.DataFrame()

    # Combinar años
    all_dims = set()
    for f in frames.values():
        all_dims.update(f[bd_dim].tolist())

    rows = []
    for dim_val in sorted(all_dims):
        row = {bd_dim: dim_val}
        for y in years:
            f = frames.get(y, pd.DataFrame())
            r = f[f[bd_dim] == dim_val]
            if len(r):
                r = r.iloc[0]
                row[f"Part. {y}"] = int(r["Participantes"])
                row[f"Horas {y}"] = round(float(r["Total_Horas"]), 1)
                row[f"h/p {y}"] = round(float(r["h_p"]), 2)
                row[f"h/HC {y}"] = round(float(r["h_hc"]), 2)
                row[f"HC {y}"] = int(r["HC_Total"])
            else:
                row[f"Part. {y}"] = 0
                row[f"Horas {y}"] = 0.0
                row[f"h/p {y}"] = 0.0
                row[f"h/HC {y}"] = 0.0
                row[f"HC {y}"] = 0

        # Variaciones
        for metric, key in [("Part.", "Part."), ("Horas", "Horas"), ("h/p", "h/p"), ("h/HC", "h/HC")]:
            v2024 = row.get(f"{metric} 2024", 0)
            v2025 = row.get(f"{metric} 2025", 0)
            row[f"Var% {metric}"] = var_pct(v2025, v2024)

        rows.append(row)

    return pd.DataFrame(rows)


# ─── Matriz Escuela × Nivel ───────────────────────────────────────────────────

def compute_cross_matrix(bd: pd.DataFrame, hc: pd.DataFrame = None, year: int = None) -> pd.DataFrame:
    """
    Matriz cruzada Escuela × Level_norm → h/HC total del nivel.
    Métrica: Total Horas (escuela, nivel) / HC total del nivel (denominador metodología IIFTO).
    Si hc es None, usa h/p entrenados como fallback.
    Si year está definido, filtra por ese año.
    """
    school_col = config.BD["school"]
    level_col = config.BD["level"]
    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]
    year_col = config.BD["year"]
    hc_year_col = config.HC["year"]

    df = bd.copy()
    if year is not None:
        df = df[df[year_col] == year]

    if len(df) == 0:
        return pd.DataFrame()

    grp = (
        df.groupby([school_col, level_col], observed=True)
        .agg(
            Participantes=(pid_col, "nunique"),
            Total_Horas=(hrs_col, "sum"),
        )
        .reset_index()
    )

    # Denominador: HC por nivel en el año correspondiente
    if hc is not None and year is not None:
        hc_yr = hc[hc[hc_year_col] == year]
        hc_by_level = hc_yr.groupby("Level_norm", observed=True).size().reset_index(name="HC_Level")
        hc_by_level = hc_by_level.rename(columns={"Level_norm": level_col})
        grp = grp.merge(hc_by_level, on=level_col, how="left")
        grp["HC_Level"] = grp["HC_Level"].fillna(1)
        grp["h_p"] = grp.apply(lambda r: safe_div(r["Total_Horas"], r["HC_Level"]), axis=1)
    else:
        # Fallback: h/p entrenados
        grp["h_p"] = grp.apply(lambda r: safe_div(r["Total_Horas"], r["Participantes"]), axis=1)

    matrix = grp.pivot_table(
        index=school_col,
        columns=level_col,
        values="h_p",
        aggfunc="sum",
        fill_value=0,
    )

    # Ordenar filas y columnas según config
    school_order = [s for s in config.SCHOOL_ORDER if s in matrix.index]
    school_order += [s for s in matrix.index if s not in school_order]
    matrix = matrix.reindex(school_order)

    level_order = [l for l in config.LEVEL_ORDER if l in matrix.columns]
    matrix = matrix.reindex(columns=level_order, fill_value=0)

    return matrix.round(2)


def compute_school_ranking(bd: pd.DataFrame, years=(2024, 2025)) -> pd.DataFrame:
    """
    Ranking de escuelas por volumen de horas, comparativa interanual.
    """
    school_col = config.BD["school"]
    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]
    year_col = config.BD["year"]

    rows = {}
    for y in years:
        bd_y = bd[bd[year_col] == y]
        grp = (
            bd_y.groupby(school_col, observed=True)
            .agg(
                Participantes=(pid_col, "nunique"),
                Total_Horas=(hrs_col, "sum"),
            )
            .reset_index()
        )
        for _, r in grp.iterrows():
            s = r[school_col]
            if s not in rows:
                rows[s] = {}
            rows[s][f"Part. {y}"] = int(r["Participantes"])
            rows[s][f"Horas {y}"] = round(float(r["Total_Horas"]), 1)

    result = []
    for school, data in rows.items():
        row = {"Escuela": school}
        row.update(data)
        h2024 = row.get("Horas 2024", 0)
        h2025 = row.get("Horas 2025", 0)
        row["Var% Horas"] = var_pct(h2025, h2024)
        result.append(row)

    df = pd.DataFrame(result)
    if "Horas 2025" in df.columns:
        df = df.sort_values("Horas 2025", ascending=False).reset_index(drop=True)

    # Rellenar NaN con 0 en columnas numéricas
    for col in [f"Part. {y}" for y in years] + [f"Horas {y}" for y in years]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df
