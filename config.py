import os

# ─── Ruta al archivo Excel ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Reporte_Formacion_CAR_TRAD.xlsx")

# ─── Nombres de columnas BD Consolidada ──────────────────────────────────────
BD = {
    "year": "Year",
    "person_id": "Person ID",
    "hours": "Total Hours",
    "date": "Date",
    "title": "Title",
    "type": "Type",
    "school": "School",
    "progress": "Progress State",
    "gender": "Gender",
    "country": "Country",
    "company": "Company",
    "bu": "Business Unit",
    "division": "Division",
    "location": "Location",
    "level": "Level_norm",
    "first_name": "Emp First Name",
    "last_name": "Emp Last Name",
}

# ─── Nombres de columnas HeadCount ───────────────────────────────────────────
HC = {
    "year": "AÑO",
    "person_id": "PERSON ID",
    "was_trained": "Was_Trained",
    "training_hours": "Total_Training_Hours",
    "country": "COUNTRY",
    "company": "COMPANY",
    "bu": "BUSINESS UNIT",
    "division": "DIVISION",
    "emp_group": "POS EMP GROUP",
    "job_level": "JOB LEVEL",
    "first_name": "EMP FIRST NAME",
    "last_name": "EMP LAST NAME",
    "gender": "EMP GENDER",
    "active": "ACTIVO",
}

# ─── Mapeo de código de país HC → nombre BD ──────────────────────────────────
HC_COUNTRY_MAP = {
    "DOM": "República Dominicana",
    "COL": "Colombia",
    "PRI": "Puerto Rico",
    "SUR": "Suriname",
    "GUF": "Guayana Francesa",
    "DMA": "Dominica",
    "SXM": "San Martín",
    "ATG": "Antigua y Barbuda",
    "VIR": "Islas Vírgenes (EE.UU.)",
    "HTI": "Haití",
    "HND": "Honduras",
}

# ─── Mapeo de JOB LEVEL HC → Level_norm BD ───────────────────────────────────
HC_LEVEL_MAP = {
    "TECHNICAL /OPERATIVES": "Technical Operative",
    "SPECIALISTS": "Specialist",
    "MIDDLE MANAGEMENT": "Middle Management",
    "HIGH MANAGEMENT": "High Management",
    "DIRECTIVE COMMITTEE": "Directive Committee",
}

# ─── Orden canónico de niveles (de mayor a menor jerarquía) ──────────────────
LEVEL_ORDER = [
    "Directive Committee",
    "High Management",
    "Middle Management",
    "Specialist",
    "Technical Operative",
    "Sin Clasificar",
]

# ─── Orden de escuelas (por volumen típico de horas) ─────────────────────────
SCHOOL_ORDER = [
    "Sostenibilidad",
    "Liderazgo y Gerencia",
    "Corporativa",
    "Cementos",
    "TI",
    "Idiomas",
    "Diversidad",
    "Finanzas",
    "Cadena de abastecimiento",
    "Concretos",
    "Academia E4",
    "Summarte",
    "Infraestructura",
]

# ─── Paleta de colores Argos ──────────────────────────────────────────────────
COLORS = {
    "primary": "#E87722",       # Naranja Argos
    "secondary": "#004B87",     # Azul oscuro
    "positive": "#2ECC71",      # Verde (variación positiva)
    "negative": "#E74C3C",      # Rojo (variación negativa)
    "neutral": "#95A5A6",       # Gris neutro
    "bg_card": "#F8F9FA",
    "year_2024": "#004B87",
    "year_2025": "#E87722",
}

# ─── Años disponibles ─────────────────────────────────────────────────────────
YEARS = [2024, 2025]
