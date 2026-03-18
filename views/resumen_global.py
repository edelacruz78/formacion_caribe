import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from metrics.calculations import compute_summary, compute_yoy_summary, fmt_var, var_pct
from components.kpi_card import kpi_card
from components.export import export_button
import config


def render(bd_f: pd.DataFrame, hc_f: pd.DataFrame, bd_all: pd.DataFrame, hc_all: pd.DataFrame):
    """Tab 1: Resumen Global — KPIs + tabla comparativa interanual."""

    if len(bd_f) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    year_col = config.BD["year"]
    hc_year_col = config.HC["year"]

    # ── Determinar si hay datos para ambos años ───────────────────────────────
    years_in_data = sorted(bd_f[year_col].dropna().unique().tolist())
    has_2024 = 2024 in years_in_data
    has_2025 = 2025 in years_in_data
    both_years = has_2024 and has_2025

    if not both_years and len(years_in_data) == 1:
        st.info(
            f"Mostrando datos solo para **{years_in_data[0]}**. "
            "Selecciona ambos años en el sidebar para ver la comparación interanual."
        )

    # ── KPIs del año más reciente disponible ─────────────────────────────────
    latest_year = max(years_in_data)
    prev_year = latest_year - 1 if (latest_year - 1) in years_in_data else None

    bd_curr = bd_f[bd_f[year_col] == latest_year]
    hc_curr = hc_f[hc_f[hc_year_col] == latest_year]
    metrics_curr = compute_summary(bd_curr, hc_curr)

    delta_part = delta_hrs = delta_hpp = delta_hhc = delta_sin = None
    if prev_year:
        bd_prev = bd_f[bd_f[year_col] == prev_year]
        hc_prev = hc_f[hc_f[hc_year_col] == prev_year]
        m_prev = compute_summary(bd_prev, hc_prev)
        delta_part = var_pct(metrics_curr["participantes"], m_prev["participantes"])
        delta_hrs = var_pct(metrics_curr["total_horas"], m_prev["total_horas"])
        delta_hpp = var_pct(metrics_curr["h_p_entrenados"], m_prev["h_p_entrenados"])
        delta_hhc = var_pct(metrics_curr["h_hc_total"], m_prev["h_hc_total"])
        delta_sin = var_pct(metrics_curr["sin_formacion"], m_prev["sin_formacion"])

    # ── Fila de KPI cards ─────────────────────────────────────────────────────
    st.subheader(f"Métricas Regionales — {latest_year}")
    cols = st.columns(5)
    with cols[0]:
        kpi_card("Participantes", metrics_curr["participantes"], delta_part,
                 format_type="number", help_text="Colaboradores únicos con al menos un curso registrado")
    with cols[1]:
        kpi_card("Total Horas", metrics_curr["total_horas"], delta_hrs,
                 format_type="hours", help_text="Suma total de horas de formación ejecutadas")
    with cols[2]:
        kpi_card("h/p Entrenados", metrics_curr["h_p_entrenados"], delta_hpp,
                 format_type="hours_pp", help_text="Horas promedio por colaborador entrenado")
    with cols[3]:
        kpi_card("h/HC Total", metrics_curr["h_hc_total"], delta_hhc,
                 format_type="hours_pp", help_text="Horas promedio por cada empleado activo (incluye no entrenados)")
    with cols[4]:
        kpi_card("Sin Formación", metrics_curr["sin_formacion"], delta_sin,
                 format_type="number", help_text="HC total menos colaboradores con registro de formación")

    st.divider()

    # ── Tabla comparativa interanual ──────────────────────────────────────────
    if both_years:
        st.subheader("Comparativa 2024 vs. 2025")
        df_yoy = compute_yoy_summary(bd_f, hc_f)

        # Tabla con formato
        display_df = df_yoy.copy()
        display_df["Var %"] = display_df["Var %"].apply(fmt_var)
        display_df["2024"] = display_df.apply(
            lambda r: _fmt_metric_val(r["Métrica"], r["2024"]), axis=1
        )
        display_df["2025"] = display_df.apply(
            lambda r: _fmt_metric_val(r["Métrica"], r["2025"]), axis=1
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Métrica": st.column_config.TextColumn("Métrica", width="large"),
                "2024": st.column_config.TextColumn("2024"),
                "2025": st.column_config.TextColumn("2025"),
                "Var %": st.column_config.TextColumn("Var %"),
            },
        )

        # ── Gráfico comparativo ───────────────────────────────────────────────
        st.subheader("Evolución de Participantes y Horas")
        _plot_comparison(bd_f, hc_f)

        # ── Exportar ──────────────────────────────────────────────────────────
        export_button(
            {"Resumen Global": df_yoy},
            filename="resumen_global.xlsx",
            key="export_resumen",
        )


def _fmt_metric_val(metric_label: str, val) -> str:
    """Formatea el valor según el tipo de métrica."""
    if val is None or pd.isna(val):
        return "—"
    if "hora" in metric_label.lower():
        return f"{float(val):,.1f} h"
    if "h/p" in metric_label.lower() or "h/hc" in metric_label.lower():
        return f"{float(val):.1f} h/p"
    return f"{int(val):,}".replace(",", ".")


def _plot_comparison(bd: pd.DataFrame, hc: pd.DataFrame):
    """Gráfico de barras doble: Participantes y Horas por año."""
    year_col = config.BD["year"]
    hc_year_col = config.HC["year"]
    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]

    data = []
    for y in [2024, 2025]:
        bd_y = bd[bd[year_col] == y]
        hc_y = hc[hc[hc_year_col] == y]
        if len(bd_y) > 0:
            data.append({
                "Año": str(y),
                "Participantes": bd_y[pid_col].nunique(),
                "Total Horas": round(bd_y[hrs_col].sum(), 1),
            })

    if not data:
        return

    col1, col2 = st.columns(2)
    colors = [config.COLORS["year_2024"], config.COLORS["year_2025"]]

    with col1:
        fig = go.Figure(go.Bar(
            x=[d["Año"] for d in data],
            y=[d["Participantes"] for d in data],
            marker_color=colors[:len(data)],
            text=[f"{d['Participantes']:,}" for d in data],
            textposition="outside",
        ))
        fig.update_layout(
            title="Participantes con formación",
            yaxis_title="Colaboradores",
            plot_bgcolor="white",
            height=300,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure(go.Bar(
            x=[d["Año"] for d in data],
            y=[d["Total Horas"] for d in data],
            marker_color=colors[:len(data)],
            text=[f"{d['Total Horas']:,.0f} h" for d in data],
            textposition="outside",
        ))
        fig2.update_layout(
            title="Total horas de formación",
            yaxis_title="Horas",
            plot_bgcolor="white",
            height=300,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)
