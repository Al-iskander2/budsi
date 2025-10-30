#!/usr/bin/env bash
set -o errexit

echo "=== INICIANDO DEPLOY ==="

# ✅ ACTUALIZAR E INSTALAR TESSERACT CORRECTAMENTE
echo "=== ACTUALIZANDO E INSTALANDO TESSERACT OCR ==="
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa libtesseract-dev

# ✅ VERIFICAR INSTALACIÓN MÁS DETALLADA
echo "=== VERIFICANDO TESSERACT ==="
if command -v tesseract > /dev/null; then
    echo "✅ Tesseract encontrado en PATH"
    tesseract --version
else
    echo "❌ Tesseract no en PATH - buscando ubicación..."
    # Buscar en ubicaciones comunes
    find /usr -name tesseract 2>/dev/null || echo "Tesseract no encontrado"
fi

# ✅ VERIFICAR LENGUAJES INSTALADOS
echo "=== VERIFICANDO LENGUAJES TESSERACT ==="
tesseract --list-langs 2>/dev/null || echo "No se pueden listar lenguajes"

echo "=== INSTALANDO DEPENDENCIAS PYTHON ==="
pip install --upgrade pip
pip install -r requirements.txt

# ✅ VERIFICAR QUE PYTESSERACT PUEDE IMPORTARSE
python -c "import pytesseract; print('✅ pytesseract importado correctamente')" || echo "❌ Error importando pytesseract"

echo "=== CONFIGURANDO ENTORNO RENDER ==="
# ✅ CORREGIR: Crear estructura de directorios consistente
mkdir -p media/invoices
mkdir -p media/logos
mkdir -p staticfiles

echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate --noinput

echo "=== COLECTANDO ARCHIVOS ESTÁTICOS ==="
python manage.py collectstatic --noinput --clear

echo "=== DEPLOY COMPLETADO ==="