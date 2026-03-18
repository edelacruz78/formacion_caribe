import streamlit as st
from metrics.calculations import fmt_var


def kpi_card(label: str, value, delta=None, format_type: str = "number", help_text: str = None):
    """
    Muestra una tarjeta KPI con st.metric.

    format_type:
        "number"   → entero con separador de miles
        "hours"    → float con 2 decimales + "h"
        "hours_pp" → float con 1 decimal + " h/p"
        "percent"  → variación porcentual
    """
    if format_type == "number":
        val_str = f"{int(value):,}".replace(",", ".")
    elif format_type == "hours":
        val_str = f"{float(value):,.1f} h".replace(",", "X").replace(".", ",").replace("X", ".")
    elif format_type == "hours_pp":
        val_str = f"{float(value):.1f} h/p"
    else:
        val_str = str(value)

    delta_str = None
    if delta is not None:
        delta_str = fmt_var(delta)

    st.metric(label=label, value=val_str, delta=delta_str, help=help_text)
