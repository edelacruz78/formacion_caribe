#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Instalación inicial y lanzamiento del Dashboard de Formación
#  Usar la PRIMERA VEZ o si hay errores con el otro lanzador
# ─────────────────────────────────────────────────────────────

cd "$(dirname "$0")"

echo "=============================================="
echo "  Dashboard Formación Caribe — Instalación"
echo "=============================================="
echo ""

# Buscar Python
PYTHON=""
for candidate in \
    "$HOME/anaconda3/bin/python3" \
    "$HOME/miniconda3/bin/python3" \
    "$HOME/opt/anaconda3/bin/python3" \
    "/usr/local/bin/python3" \
    "$(which python3)"; do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        echo "✓ Python encontrado: $PYTHON"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "ERROR: No se encontró Python."
    echo "Por favor instala Anaconda desde: https://www.anaconda.com"
    osascript -e 'display alert "Python no encontrado" message "Descarga e instala Anaconda desde anaconda.com, luego vuelve a ejecutar este archivo." buttons {"Abrir anaconda.com", "Cancelar"} default button 1' | grep -q "Abrir" && open "https://www.anaconda.com"
    read -p "Presiona Enter para salir..."
    exit 1
fi

echo ""
echo "Instalando/actualizando dependencias..."
$PYTHON -m pip install streamlit plotly xlsxwriter openpyxl --quiet --upgrade
echo "✓ Dependencias listas"

echo ""
echo "Iniciando Dashboard..."
$PYTHON -m streamlit run app.py \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.port 8501 &

# Esperar que arranque
echo "Esperando que el servidor inicie..."
for i in $(seq 1 20); do
    sleep 1
    echo -n "."
    if lsof -i :8501 &>/dev/null; then
        echo ""
        echo "✓ Dashboard activo"
        break
    fi
done

open "http://localhost:8501"
echo ""
echo "Abriendo en el browser: http://localhost:8501"
echo ""
echo "Para cerrar el dashboard: cierra esta ventana o presiona Ctrl+C"
wait
