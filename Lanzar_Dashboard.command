#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Lanzar Dashboard de Formación Caribe
#  Doble clic en este archivo para abrir el dashboard
# ─────────────────────────────────────────────────────────────

# Ir a la carpeta donde está el app
cd "$(dirname "$0")"

# Buscar Python de Anaconda o Python del sistema
PYTHON=""
for candidate in \
    "$HOME/anaconda3/bin/python3" \
    "$HOME/miniconda3/bin/python3" \
    "$HOME/opt/anaconda3/bin/python3" \
    "$(which python3)" \
    "$(which python)"; do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Error" message "No se encontró Python. Por favor instala Anaconda desde anaconda.com y vuelve a intentar." buttons {"OK"} default button 1'
    exit 1
fi

# Instalar dependencias si faltan
echo "Verificando dependencias..."
$PYTHON -c "import streamlit" 2>/dev/null || $PYTHON -m pip install streamlit plotly xlsxwriter openpyxl --quiet

# Verificar si ya hay una instancia corriendo
if lsof -i :8501 &>/dev/null; then
    # Ya está corriendo, solo abrir el browser
    open "http://localhost:8501"
else
    # Lanzar Streamlit
    echo "Iniciando Dashboard..."
    $PYTHON -m streamlit run app.py \
        --server.headless true \
        --browser.gatherUsageStats false \
        --server.port 8501 &

    # Esperar a que arranque (máx 15 segundos)
    for i in $(seq 1 15); do
        sleep 1
        if lsof -i :8501 &>/dev/null; then
            break
        fi
    done

    # Abrir el browser
    open "http://localhost:8501"
fi

echo "Dashboard activo en http://localhost:8501"
