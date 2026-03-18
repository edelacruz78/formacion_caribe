import io
import pandas as pd
import streamlit as st
from metrics.calculations import fmt_var


def _format_df_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas de Var% (float) a string legible para el Excel exportado."""
    df = df.copy()
    for col in df.columns:
        if "Var%" in col or "Var %" in col:
            df[col] = df[col].apply(fmt_var)
    return df


def export_button(
    dfs: dict,
    filename: str,
    label: str = "⬇️ Exportar a Excel",
    key: str = None,
):
    """
    Crea un botón de descarga que genera un archivo .xlsx con múltiples hojas.

    dfs: {"Nombre de hoja": dataframe, ...}
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for sheet_name, df in dfs.items():
            df_export = _format_df_for_export(df)
            # Limitar nombre de hoja a 31 caracteres (límite Excel)
            safe_name = sheet_name[:31]
            df_export.to_excel(writer, sheet_name=safe_name, index=False)

            workbook = writer.book
            worksheet = writer.sheets[safe_name]

            # Formato de encabezado
            header_fmt = workbook.add_format({
                "bold": True,
                "bg_color": "#004B87",
                "font_color": "#FFFFFF",
                "border": 1,
                "align": "center",
            })
            # Formato de fila alternada
            alt_fmt = workbook.add_format({"bg_color": "#F2F7FC", "border": 1})
            normal_fmt = workbook.add_format({"border": 1})

            # Escribir encabezados con formato
            for col_num, col_name in enumerate(df_export.columns):
                worksheet.write(0, col_num, col_name, header_fmt)

            # Auto-ajustar ancho de columnas
            for col_num, col_name in enumerate(df_export.columns):
                max_len = max(
                    df_export[col_name].astype(str).map(len).max(),
                    len(str(col_name)),
                ) + 3
                worksheet.set_column(col_num, col_num, min(max_len, 40))

            # Formato alternado en filas
            for row_num in range(1, len(df_export) + 1):
                fmt = alt_fmt if row_num % 2 == 0 else normal_fmt
                for col_num in range(len(df_export.columns)):
                    cell_val = df_export.iloc[row_num - 1, col_num]
                    worksheet.write(row_num, col_num, cell_val, fmt)

    buffer.seek(0)
    st.download_button(
        label=label,
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key,
    )
