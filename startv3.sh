#!/bin/bash
# start.sh - Arranca ambos servicios con entorno virtual automático y logs combinados

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  QR-GYM - ARRANQUE DE SERVICIOS${NC}"
echo -e "${GREEN}========================================${NC}"

# --- 1. Crear entorno virtual si no existe ---
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}▶ Creando entorno virtual en $VENV_DIR...${NC}"
    python3 -m venv --system-site-packages "$VENV_DIR"
    echo -e "${GREEN}✔ Entorno virtual creado.${NC}"
else
    echo -e "${YELLOW}▶ Usando entorno virtual existente en $VENV_DIR.${NC}"
fi

# --- 2. Activar entorno virtual e instalar dependencias pip ---
source "$VENV_DIR/bin/activate"

echo -e "${YELLOW}▶ Instalando dependencias pip desde requirements.txt...${NC}"
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo -e "${GREEN}✔ Dependencias pip instaladas.${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró requirements.txt, omitiendo.${NC}"
fi

# --- 3. Verificar que los scripts existen ---
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py no encontrado${NC}"
    exit 1
fi
if [ ! -f "hardware/acceso.py" ]; then
    echo -e "${RED}Error: hardware/acceso.py no encontrado${NC}"
    exit 1
fi

# --- 4. Función para limpiar al salir (Ctrl+C) ---
cleanup() {
    echo -e "\n${YELLOW}Deteniendo servicios...${NC}"
    kill $WEB_PID $ACCESO_PID 2>/dev/null || true
    wait $WEB_PID $ACCESO_PID 2>/dev/null || true
    echo -e "${GREEN}Servicios detenidos.${NC}"
    deactivate
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- 5. Iniciar servicios en background ---
echo -e "${YELLOW}▶ Iniciando app web...${NC}"
python app.py > web.log 2>&1 &
WEB_PID=$!
echo -e "   Web PID: $WEB_PID (logs en web.log)"

echo -e "${YELLOW}▶ Iniciando control de acceso...${NC}"
PYTHONPATH=. python hardware/acceso.py > acceso.log 2>&1 &
ACCESO_PID=$!
echo -e "   Acceso PID: $ACCESO_PID (logs en acceso.log)"

echo -e "${GREEN}✔ Servicios iniciados. Mostrando logs en tiempo real (Ctrl+C para salir).${NC}"
echo -e "${GREEN}========================================${NC}"

# --- 6. Mostrar logs combinados ---
tail -f web.log acceso.log
