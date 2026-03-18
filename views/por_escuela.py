import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from metrics.calculations import compute_school_ranking, compute_cross_matrix, fmt_var
from components.export import export_button
import config


def render(bd_f: pd.DataFrame, hc_f: pd.DataFrame):
    """Tab 4: Análisis por Escuela de Formación."""

    if len(bd_f) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    st.subheader("Análisis por Escuela de Formación")

    # ── Ranking de escuelas ───────────────────────────────────────────────────
    st.markdown("#### Ranking de Escuelas por Volumen de Horas")

    df_rank = compute_school_ranking(bd_f)

    if df_rank.empty:
        st.warning("No hay datos de escuelas para mostrar.")
        return

    # Tabla de ranking
    display_rank = df_rank.copy()
    if "Var% Horas" in display_rank.columns:
        display_rank["Var% Horas"] = display_rank["Var% Horas"].apply(fmt_var)

    col_config = {
        "Escuela": st.column_config.TextColumn("Escuela", width="medium"),
        "Part. 2024": st.column_config.NumberColumn("Part. 2024", format="%d"),
        "Part. 2025": st.column_config.NumberColumn("Part. 2025", format="%d"),
        "Horas 2024": st.column_config.NumberColumn("Horas 2024", format="%.1f"),
        "Horas 2025": st.column_config.NumberColumn("Horas 2025", format="%.1f"),
        "Var% Horas": st.column_config.TextColumn("Var% Horas"),
    }
    st.dataframe(display_rank, use_container_width=True, hide_index=True, column_config=col_config)

    # Gráfico ranking
    _plot_school_ranking(df_rank)

    st.divider()

    # ── Matriz cruzada Escuela × Nivel ────────────────────────────────────────
    st.markdown("#### Matriz: h/p por Escuela y Nivel Jerárquico")

    year_col = config.BD["year"]
    years_available = sorted(bd_f[year_col].dropna().unique().tolist())

    if len(years_available) > 1:
        year_sel = st.selectbox(
            "Año para la matriz:",
            options=years_available,
            index=len(years_available) - 1,
            key="matrix_year_select",
        )
    else:
        year_sel = years_available[0] if years_available else None

    if year_sel:
        matrix = compute_cross_matrix(bd_f, hc=hc_f, year=int(year_sel))

        if not matrix.empty:
            # Heatmap con Plotly
            _plot_heatmap(matrix, year_sel)

            # Tabla numérica
            with st.expander("Ver tabla de valores (h/p)"):
                matrix_display = matrix.copy()
                # Reemplazar 0 con "—" para mejor legibilidad
                matrix_display = matrix_display.applymap(
                    lambda x: f"{x:.1f}" if x > 0 else "—"
                )
                st.dataframe(matrix_display, use_container_width=True)

    # ── Exportar ──────────────────────────────────────────────────────────────
    export_dfs = {"Ranking Escuelas": df_rank}
    if year_sel and not matrix.empty:
        export_dfs[f"Matriz {year_sel}"] = matrix.reset_index()

    export_button(
        export_dfs,
        filename="analisis_por_escuela.xlsx",
        key="export_escuela",
    )


def _plot_school_ranking(df: pd.DataFrame):
    """Gráfico de barras horizontales del ranking de escuelas."""
    col2024 = "Horas 2024" if "Horas 2024" in df.columns else None
    col2025 = "Horas 2025" if "Horas 2025" in df.columns else None

    if not col2025:
        return

    df_plot = df[["Escuela", col2024, col2025]].fillna(0) if col2024 else df[["Escuela", col2025]].fillna(0)
    df_plot = df_plot.sort_values(col2025, ascending=True)

    fig = go.Figure()
    if col2024:
        fig.add_trace(go.Bar(
            y=df_plot["Escuela"],
            x=df_plot[col2024],
            name="2024",
            orientation="h",
            marker_color=config.COLORS["year_2024"],
            opacity=0.85,
        ))
    fig.add_trace(go.Bar(
        y=df_plot["Escuela"],
        x=df_plot[col2025],
        name="2025",
        orientation="h",
        marker_color=config.COLORS["year_2025"],
        opacity=0.85,
    ))

    fig.update_layout(
        title="Ranking de Escuelas — Horas de Formación",
        xaxis_title="Horas",
        barmode="group",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=1.05),
        height=max(350, len(df_plot) * 35 + 120),
        margin=dict(l=200, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _plot_heatmap(matrix: pd.DataFrame, year: int):
    """Heatmap de la matriz Escuela × Nivel."""
    # Reemplazar 0 con NaN para que aparezca en blanco
    z_data = matrix.values.copy().astype(float)
    z_display = np.where(z_data == 0, np.nan, z_data)

    text_data = []
    for row in z_data:
        text_row = []
        for val in row:
            text_row.append(f"{val:.1f}" if val > 0 else "—")
        text_data.append(text_row)

    fig = go.Figure(go.Heatmap(
        z=z_display,
        x=list(matrix.columns),
        y=list(matrix.index),
        text=text_data,
        texttemplate="%{text}",
        colorscale=[
            [0.0, "#FFFFFF"],
            [0.01, "#D6EAF8"],
            [0.3, "#7FB3D3"],
            [0.6, "#2E86C1"],
            [1.0, "#1A5276"],
        ],
        showscale=True,
        colorbar=dict(title="h/p"),
        xgap=2,
        ygap=2,
    ))

    fig.update_layout(
        title=f"h/p por Escuela y Nivel Jerárquico — {year}",
        xaxis=dict(side="top", tickangle=-30),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white",
        height=max(350, len(matrix) * 35 + 150),
        margin=dict(l=200, r=40, t=100, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Leyenda de colores
    st.caption(
        "Color: más intenso = mayor intensidad formativa (h/p). "
        "Blanco / — = sin registros de formación en esa combinación."
    )
