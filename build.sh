#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

# ✅ DETECTAR ENTORNO Y ACTUAR EN CONSECUENCIA
if [ -z "$RENDER" ]; then
    echo "=== ENTORNO LOCAL: Instalando Tesseract con sudo ==="
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
else
    echo "=== ENTORNO RENDER: Instalando Tesseract sin sudo ==="
    apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
fi

# ✅ VERIFICAR TESSERACT
echo "=== VERIFICANDO TESSERACT ==="
if command -v tesseract &> /dev/null; then
    tesseract --version
    echo "✅ Tesseract disponible"
else
    echo "❌ Tesseract NO disponible - Intentando alternativas..."
    
    # Buscar Tesseract en ubicaciones alternativas
    if [ -f "/usr/bin/tesseract" ]; then
        echo "✅ Tesseract encontrado en /usr/bin/tesseract"
    elif [ -f "/usr/local/bin/tesseract" ]; then
        echo "✅ Tesseract encontrado en /usr/local/bin/tesseract"
    else
        echo "⚠️  Tesseract no encontrado - OCR usará valores por defecto"
    fi
fi

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