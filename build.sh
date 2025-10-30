#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

# ✅ INSTALAR TESSERACT OCR - VERSIÓN CORREGIDA
echo "=== INSTALANDO TESSERACT OCR ==="
sudo apt-get update
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-eng  # Idioma inglés
sudo apt-get install -y tesseract-ocr-spa  # Idioma español (opcional)

# ✅ VERIFICAR INSTALACIÓN DE TESSERACT
echo "=== VERIFICANDO TESSERACT ==="
which tesseract
tesseract --version
echo "Tesseract instalado correctamente"

# ✅ INSTALAR DEPENDENCIAS PYTHON
echo "=== INSTALANDO DEPENDENCIAS PYTHON ==="
pip install pytesseract
pip install opencv-python-headless
pip install -r requirements.txt

# ✅ CONFIGURAR DIRECTORIOS PARA RENDER
if [ "$RENDER" ]; then
    echo "=== CONFIGURANDO ENTORNO RENDER ==="
    # Crear directorio para archivos media
    mkdir -p mediafiles
    chmod -R 755 mediafiles
    
    # Crear directorio para archivos estáticos si no existe
    mkdir -p staticfiles
    chmod -R 755 staticfiles
    
    echo "Directorios creados: mediafiles, staticfiles"
fi

# ✅ APLICAR MIGRACIONES
echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate --noinput

# ✅ COLECTAR ARCHIVOS ESTÁTICOS
echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput --clear

# ✅ VERIFICAR ESTRUCTURA DE DIRECTORIOS
echo "=== VERIFICANDO ESTRUCTURA ==="
ls -la
if [ "$RENDER" ]; then
    echo "=== CONTENIDO DE MEDIAFILES ==="
    ls -la mediafiles/
    echo "=== CONTENIDO DE STATICFILES ==="
    ls -la staticfiles/
fi

echo "=== DEPLOY COMPLETADO ==="