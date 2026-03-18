import streamlit as st
import pandas as pd

from metrics.calculations import safe_div
from components.export import export_button
import config


def render(bd_f: pd.DataFrame):
    """Tab 5: Búsqueda y detalle por colaborador individual."""

    st.subheader("Búsqueda por Colaborador")
    st.caption(
        "Busca por nombre, apellido o ID de empleado. "
        "Los resultados respetan los filtros activos en el sidebar."
    )

    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]
    level_col = config.BD["level"]
    country_col = config.BD["country"]
    school_col = config.BD["school"]
    year_col = config.BD["year"]

    # ── Buscador ──────────────────────────────────────────────────────────────
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        query = st.text_input(
            "Nombre, apellido o ID:",
            placeholder="Ej: García / 2000001234",
            key="colab_search_input",
            label_visibility="collapsed",
        )
    with col_btn:
        buscar = st.button("Buscar", use_container_width=True, key="colab_search_btn")

    if not query:
        # Mostrar top 10 colaboradores por horas en año más reciente
        st.markdown("---")
        _show_top_collaborators(bd_f)
        return

    # ── Aplicar búsqueda ──────────────────────────────────────────────────────
    query_str = str(query).strip()

    # Intentar búsqueda por ID numérico
    try:
        pid_query = int(query_str)
        mask = bd_f[pid_col] == pid_query
    except ValueError:
        # Búsqueda por nombre (insensible a mayúsculas)
        mask = bd_f["Nombre Completo"].str.contains(query_str, case=False, na=False)

    results = bd_f[mask]

    if len(results) == 0:
        st.warning(f"No se encontraron registros para **'{query_str}'**.")
        return

    # ── Lista de coincidencias (si hay más de una persona) ────────────────────
    unique_persons = results[[pid_col, "Nombre Completo", level_col, country_col]].drop_duplicates(pid_col)

    if len(unique_persons) > 1:
        st.info(f"Se encontraron **{len(unique_persons)}** colaboradores. Selecciona uno:")
        person_options = {
            f"{row['Nombre Completo']} (ID: {row[pid_col]})": row[pid_col]
            for _, row in unique_persons.iterrows()
        }
        selected_label = st.selectbox("Colaborador:", list(person_options.keys()), key="colab_select")
        selected_pid = person_options[selected_label]
        person_data = results[results[pid_col] == selected_pid]
    else:
        selected_pid = unique_persons.iloc[0][pid_col]
        person_data = results

    # ── Perfil del colaborador ────────────────────────────────────────────────
    _show_person_profile(person_data, selected_pid)

    # ── Exportar ──────────────────────────────────────────────────────────────
    export_cols = [year_col, "Date", "Title", school_col, "Type", hrs_col, "Progress State"]
    export_df = person_data[[c for c in export_cols if c in person_data.columns]].copy()
    export_df = export_df.rename(columns={
        year_col: "Año",
        "Date": "Fecha",
        "Title": "Curso",
        school_col: "Escuela",
        "Type": "Modalidad",
        hrs_col: "Horas",
        "Progress State": "Estado",
    })

    nombre = person_data["Nombre Completo"].iloc[0].replace(" ", "_")
    export_button(
        {"Historial Formación": export_df},
        filename=f"formacion_{nombre}.xlsx",
        key="export_colaborador",
    )


def _show_person_profile(data: pd.DataFrame, pid):
    """Muestra el perfil y detalle de cursos de un colaborador."""
    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]
    level_col = config.BD["level"]
    country_col = config.BD["country"]
    school_col = config.BD["school"]
    year_col = config.BD["year"]

    nombre = data["Nombre Completo"].iloc[0]
    nivel = data[level_col].iloc[0]
    pais = data[country_col].iloc[0]
    empresa = data[config.BD["company"]].iloc[0] if config.BD["company"] in data.columns else "—"

    total_horas = float(data[hrs_col].sum())
    total_cursos = len(data)
    years = sorted(data[year_col].dropna().unique().tolist())

    st.markdown(f"### {nombre}")
    st.caption(f"ID: {pid} | Nivel: {nivel} | País: {pais} | Empresa: {empresa}")

    # KPIs del colaborador
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Horas", f"{total_horas:.1f} h")
    with cols[1]:
        st.metric("Cursos registrados", f"{total_cursos}")
    with cols[2]:
        st.metric("Años con formación", ", ".join(str(y) for y in years))
    with cols[3]:
        escuelas = data[school_col].nunique()
        st.metric("Escuelas distintas", f"{escuelas}")

    st.markdown("---")

    # Tabla de detalle de cursos
    st.markdown("#### Detalle de Cursos")
    detail_cols = [year_col, "Date", "Title", school_col, "Type", hrs_col, "Progress State"]
    detail = data[[c for c in detail_cols if c in data.columns]].copy()
    detail = detail.rename(columns={
        year_col: "Año",
        "Date": "Fecha",
        "Title": "Curso",
        school_col: "Escuela",
        "Type": "Modalidad",
        hrs_col: "Horas",
        "Progress State": "Estado",
    })
    detail = detail.sort_values(["Año", "Fecha"], ascending=[False, False])

    # Truncar título largo
    if "Curso" in detail.columns:
        detail["Curso"] = detail["Curso"].astype(str).str[:80]

    st.dataframe(
        detail,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Año": st.column_config.NumberColumn("Año", format="%d"),
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "Horas": st.column_config.NumberColumn("Horas", format="%.1f"),
        },
    )


def _show_top_collaborators(bd: pd.DataFrame):
    """Muestra top 10 colaboradores por horas en el año más reciente."""
    year_col = config.BD["year"]
    pid_col = config.BD["person_id"]
    hrs_col = config.BD["hours"]
    level_col = config.BD["level"]
    country_col = config.BD["country"]

    if len(bd) == 0:
        return

    latest_year = int(bd[year_col].max())
    bd_yr = bd[bd[year_col] == latest_year]

    st.markdown(f"#### Top 10 Colaboradores por Horas — {latest_year}")

    top = (
        bd_yr.groupby([pid_col, "Nombre Completo", level_col, country_col], observed=True)
        .agg(Total_Horas=(hrs_col, "sum"), Cursos=(hrs_col, "count"))
        .reset_index()
        .sort_values("Total_Horas", ascending=False)
        .head(10)
    )
    top = top.rename(columns={
        pid_col: "ID",
        "Nombre Completo": "Nombre",
        level_col: "Nivel",
        country_col: "País",
        "Total_Horas": "Total Horas",
        "Cursos": "# Cursos",
    })

    st.dataframe(
        top,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", format="%d"),
            "Total Horas": st.column_config.NumberColumn("Total Horas", format="%.1f h"),
        },
    )
