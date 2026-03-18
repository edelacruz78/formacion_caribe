import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from metrics.calculations import compute_by_dimension, fmt_var
from components.export import export_button
import config


def render(bd_f: pd.DataFrame, hc_f: pd.DataFrame):
    """Tab 3: Análisis por Nivel Jerárquico (Job Level)."""

    if len(bd_f) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    st.subheader("Análisis por Nivel Jerárquico")

    level_col = config.BD["level"]
    df = compute_by_dimension(bd_f, hc_f, bd_dim=level_col, hc_dim="Level_norm")

    if df.empty:
        st.warning("No hay datos suficientes.")
        return

    # Ordenar por jerarquía
    level_order = config.LEVEL_ORDER
    df["_order"] = df[level_col].map({v: i for i, v in enumerate(level_order)}).fillna(99)
    df = df.sort_values("_order").drop(columns="_order")

    # ── Tabla ─────────────────────────────────────────────────────────────────
    st.markdown("#### Participantes, Horas y h/p por Nivel (2024 vs. 2025)")

    cols_show = [level_col]
    for y in [2024, 2025]:
        for c in [f"Part. {y}", f"Horas {y}", f"h/p {y}", f"h/HC {y}", f"HC {y}"]:
            if c in df.columns:
                cols_show.append(c)
    for c in ["Var% Horas", "Var% h/HC"]:
        if c in df.columns:
            cols_show.append(c)

    display_df = df[[c for c in cols_show if c in df.columns]].copy()
    for col in display_df.columns:
        if "Var%" in col:
            display_df[col] = display_df[col].apply(fmt_var)

    display_df = display_df.rename(columns={level_col: "Nivel Jerárquico"})

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nivel Jerárquico": st.column_config.TextColumn("Nivel Jerárquico", width="medium"),
            "Part. 2024": st.column_config.NumberColumn("Part. 2024", format="%d"),
            "Part. 2025": st.column_config.NumberColumn("Part. 2025", format="%d"),
            "Horas 2024": st.column_config.NumberColumn("Horas 2024", format="%.1f h"),
            "Horas 2025": st.column_config.NumberColumn("Horas 2025", format="%.1f h"),
            "h/p 2024": st.column_config.NumberColumn("h/p 2024", format="%.2f"),
            "h/p 2025": st.column_config.NumberColumn("h/p 2025", format="%.2f"),
            "h/HC 2024": st.column_config.NumberColumn("h/HC 2024", format="%.2f"),
            "h/HC 2025": st.column_config.NumberColumn("h/HC 2025", format="%.2f"),
        },
    )

    # ── Insight automático ────────────────────────────────────────────────────
    _show_insight(df, level_col)

    # ── Gráficos ──────────────────────────────────────────────────────────────
    st.markdown("#### Visualización")
    metric_opt = st.radio(
        "Métrica:",
        ["Total Horas", "h/p Entrenados", "h/HC Total"],
        horizontal=True,
        key="nivel_metric_radio",
    )
    _plot_by_level(df, level_col, metric_opt)

    # ── Exportar ──────────────────────────────────────────────────────────────
    export_button(
        {"Por Nivel": df},
        filename="analisis_por_nivel.xlsx",
        key="export_nivel",
    )


def _show_insight(df: pd.DataFrame, level_col: str):
    """Muestra insight sobre la brecha entre niveles."""
    if "h/HC 2025" not in df.columns:
        return
    df_valid = df[df["h/HC 2025"] > 0]
    if len(df_valid) < 2:
        return
    max_row = df_valid.loc[df_valid["h/HC 2025"].idxmax()]
    min_row = df_valid.loc[df_valid["h/HC 2025"].idxmin()]
    ratio = max_row["h/HC 2025"] / min_row["h/HC 2025"] if min_row["h/HC 2025"] > 0 else 0
    if ratio > 1:
        st.info(
            f"**Brecha formativa:** El nivel **{max_row[level_col]}** recibe "
            f"{max_row['h/HC 2025']:.1f} h/HC en 2025, vs. "
            f"{min_row['h/HC 2025']:.1f} h/HC en **{min_row[level_col]}** "
            f"({ratio:.1f}x más formación)."
        )


def _plot_by_level(df: pd.DataFrame, level_col: str, metric_opt: str):
    if metric_opt == "Total Horas":
        col2024, col2025 = "Horas 2024", "Horas 2025"
        xaxis = "Horas de formación"
    elif metric_opt == "h/p Entrenados":
        col2024, col2025 = "h/p 2024", "h/p 2025"
        xaxis = "h/persona entrenado"
    else:
        col2024, col2025 = "h/HC 2024", "h/HC 2025"
        xaxis = "h/HC total"

    # Ordenar de menor a mayor para visualización horizontal
    df_plot = df[[level_col, col2024, col2025]].fillna(0)
    df_plot = df_plot.sort_values(col2025, ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_plot[level_col],
        x=df_plot[col2024],
        name="2024",
        orientation="h",
        marker_color=config.COLORS["year_2024"],
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        y=df_plot[level_col],
        x=df_plot[col2025],
        name="2025",
        orientation="h",
        marker_color=config.COLORS["year_2025"],
        opacity=0.85,
    ))

    fig.update_layout(
        title=f"{metric_opt} por Nivel Jerárquico",
        xaxis_title=xaxis,
        barmode="group",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=1.1),
        height=350,
        margin=dict(l=160, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
