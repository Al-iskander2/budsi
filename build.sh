#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

echo "=== INSTALANDO DEPENDENCIAS PYTHON ==="
pip install -r requirements.txt
pip install pytesseract opencv-python-headless

echo "=== CONFIGURANDO ENTORNO RENDER ==="
mkdir -p mediafiles
mkdir -p staticfiles

echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate --noinput

echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput --clear

echo "=== DEPLOY COMPLETADO ==="