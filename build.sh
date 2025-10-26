#!/usr/bin/env bash
set -o errexit

echo "=== INSTALANDO DEPENDENCIAS ==="
pip install -r requirements.txt

echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput

echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate

echo "✅ Build completado exitosamente!"