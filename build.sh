#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

# Instalar Tesseract OCR para Render - FORMA CORRECTA
echo "=== INSTALANDO TESSERACT OCR ==="
pip install pytesseract
pip install opencv-python-headless

# Instalar dependencias de Python
echo "=== INSTALANDO DEPENDENCIAS PYTHON ==="
pip install -r requirements.txt

# Crear directorio temporal para media en Render
if [ "$RENDER" ]; then
    echo "=== CONFIGURANDO ENTORNO RENDER ==="
    mkdir -p /tmp/media
    chmod -R 755 /tmp/media
fi

# Aplicar migraciones
echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate --noinput

# Colectar archivos estáticos
echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput

echo "=== DEPLOY COMPLETADO ==="