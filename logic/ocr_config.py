import os
import pytesseract

def configure_ocr():
    """Configura Tesseract para Render/Producción"""
    if os.environ.get('RENDER'):
        # En Render, usar Tesseract incluido con pytesseract
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    else:
        # En desarrollo, usar configuración local
        try:
            pytesseract.get_tesseract_version()
        except:
            # Fallback para desarrollo sin Tesseract
            pass

# Llamar esta función al inicio de tu aplicación
configure_ocr()