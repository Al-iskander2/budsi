#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

# ✅ DETECTAR ENTORNO Y ACTUAR EN CONSECUENCIA
if [ -z "$RENDER" ]; then
    echo "=== ENTORNO LOCAL: Instalando Tesseract ==="
    # Local - con sudo
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
else
    echo "=== ENTORNO RENDER: Usando Tesseract preinstalado ==="
    # Render - verificar si Tesseract está disponible
    if ! command -v tesseract &> /dev/null; then
        echo "⚠️  Tesseract no encontrado, intentando instalar sin sudo..."
        apt-get update || true
        apt-get install -y tesseract-ocr || echo "❌ No se pudo instalar Tesseract"
    fi
fi

# ✅ VERIFICAR TESSERACT
echo "=== VERIFICANDO TESSERACT ==="
if command -v tesseract &> /dev/null; then
    tesseract --version
    echo "✅ Tesseract disponible"
else
    echo "⚠️  Tesseract NO disponible - OCR no funcionará"
fi

# ✅ INSTALAR DEPENDENCIAS PYTHON
echo "=== INSTALANDO DEPENDENCIAS PYTHON ==="
pip install -r requirements.txt
pip install pytesseract opencv-python-headless

# ✅ CONFIGURAR DIRECTORIOS
if [ "$RENDER" ]; then
    echo "=== CONFIGURANDO ENTORNO RENDER ==="
    mkdir -p mediafiles
    mkdir -p staticfiles
    chmod -R 755 mediafiles
    chmod -R 755 staticfiles
    echo "✅ Directorios creados para Render"
fi

# ✅ APLICAR MIGRACIONES
echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate --noinput

# ✅ COLECTAR ARCHIVOS ESTÁTICOS
echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput --clear

# ✅ VERIFICAR ESTRUCTURA
echo "=== VERIFICANDO ESTRUCTURA ==="
ls -la
if [ "$RENDER" ]; then
    echo "=== CONTENIDO DE MEDIAFILES ==="
    ls -la mediafiles/ || echo "❌ No se pudo listar mediafiles"
    echo "=== CONTENIDO DE STATICFILES ==="
    ls -la staticfiles/ || echo "❌ No se pudo listar staticfiles"
fi

echo "=== DEPLOY COMPLETADO ==="