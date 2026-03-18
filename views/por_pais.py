import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from metrics.calculations import compute_by_dimension, fmt_var
from components.export import export_button
import config


def render(bd_f: pd.DataFrame, hc_f: pd.DataFrame):
    """Tab 2: Análisis por País/Operación."""

    if len(bd_f) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    st.subheader("Comparativa por País / Operación")

    country_col = config.BD["country"]
    df = compute_by_dimension(bd_f, hc_f, bd_dim=country_col, hc_dim="Country")

    if df.empty:
        st.warning("No hay datos suficientes para mostrar la comparativa.")
        return

    # ── Tabla ─────────────────────────────────────────────────────────────────
    st.markdown("#### Participantes y Horas por País (2024 vs. 2025)")

    # Seleccionar columnas relevantes para mostrar
    cols_show = [country_col]
    for y in [2024, 2025]:
        for c in [f"Part. {y}", f"Horas {y}", f"HC {y}"]:
            if c in df.columns:
                cols_show.append(c)
    for c in ["Var% Part.", "Var% Horas"]:
        if c in df.columns:
            cols_show.append(c)

    display_df = df[cols_show].copy()

    # Formatear variaciones
    for col in display_df.columns:
        if "Var%" in col:
            display_df[col] = display_df[col].apply(fmt_var)

    # Renombrar columna de país
    display_df = display_df.rename(columns={country_col: "País"})

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "País": st.column_config.TextColumn("País", width="medium"),
            "Part. 2024": st.column_config.NumberColumn("Part. 2024", format="%d"),
            "Part. 2025": st.column_config.NumberColumn("Part. 2025", format="%d"),
            "Horas 2024": st.column_config.NumberColumn("Horas 2024", format="%.1f"),
            "Horas 2025": st.column_config.NumberColumn("Horas 2025", format="%.1f"),
            "HC 2024": st.column_config.NumberColumn("HC 2024", format="%d"),
            "HC 2025": st.column_config.NumberColumn("HC 2025", format="%d"),
            "Var% Part.": st.column_config.TextColumn("Var% Part."),
            "Var% Horas": st.column_config.TextColumn("Var% Horas"),
        },
    )

    # ── Gráficos ──────────────────────────────────────────────────────────────
    st.markdown("#### Visualización")
    metric_opt = st.radio(
        "Métrica a visualizar:",
        ["Participantes", "Horas de formación", "h/HC total"],
        horizontal=True,
        key="pais_metric_radio",
    )

    _plot_by_country(df, country_col, metric_opt)

    # ── Exportar ──────────────────────────────────────────────────────────────
    export_button(
        {"Por País": df},
        filename="analisis_por_pais.xlsx",
        key="export_pais",
    )


def _plot_by_country(df: pd.DataFrame, country_col: str, metric_opt: str):
    if metric_opt == "Participantes":
        col2024, col2025 = "Part. 2024", "Part. 2025"
        yaxis_title = "Colaboradores"
        title = "Participantes con formación por País"
    elif metric_opt == "Horas de formación":
        col2024, col2025 = "Horas 2024", "Horas 2025"
        yaxis_title = "Horas"
        title = "Total horas de formación por País"
    else:
        col2024, col2025 = "h/HC 2024", "h/HC 2025"
        yaxis_title = "h/HC total"
        title = "h/HC total por País"

    df_plot = df[[country_col, col2024, col2025]].fillna(0)
    df_plot = df_plot.sort_values(col2025, ascending=True)

    fig = go.Figure()
    if col2024 in df_plot.columns:
        fig.add_trace(go.Bar(
            y=df_plot[country_col],
            x=df_plot[col2024],
            name="2024",
            orientation="h",
            marker_color=config.COLORS["year_2024"],
            opacity=0.85,
        ))
    if col2025 in df_plot.columns:
        fig.add_trace(go.Bar(
            y=df_plot[country_col],
            x=df_plot[col2025],
            name="2025",
            orientation="h",
            marker_color=config.COLORS["year_2025"],
            opacity=0.85,
        ))

    fig.update_layout(
        title=title,
        xaxis_title=yaxis_title,
        barmode="group",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=1.1),
        height=max(300, len(df_plot) * 40 + 100),
        margin=dict(l=180, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
