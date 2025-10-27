#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

# Instalar dependencias
pip install -r requirements.txt

#  CREAR DIRECTORIO TEMPORAL PARA MEDIA EN RENDER
if [ "$RENDER" ]; then
    echo "=== CREANDO DIRECTORIO TEMPORAL PARA MEDIA ==="
    mkdir -p /tmp/media
    chmod -R 755 /tmp/media
    echo "=== DIRECTORIO CREADO: /tmp/media ==="
fi

# VERIFICAR ESTADO ANTES
echo "=== ESTADO DE MIGRACIONES (ANTES) ==="
python manage.py showmigrations --list

# Aplicar migraciones
echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate --noinput

# VERIFICAR ESTADO DESPUÉS
echo "=== ESTADO DE MIGRACIONES (DESPUÉS) ==="
python manage.py showmigrations --list

# Colectar archivos estáticos
echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput

echo "=== DEPLOY COMPLETADO ==="