import re
import os
import platform
from typing import Tuple, List
from decimal import Decimal
from datetime import datetime
import fitz  # PyMuPDF - ✅ REEMPLAZA pdf2image
from PIL import Image, ImageEnhance, ImageFilter
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# Configuración Tesseract (mantener para compatibilidad)
# =============================================================================

def _maybe_set_tesseract_path():
    """
    Try to set a Tesseract path only if it exists.
    On Windows, use the typical path; on macOS/Linux, avoid changing if already in PATH.
    """
    if platform.system() == 'Windows':
        win_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        ]
        for p in win_paths:
            if os.path.exists(p):
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = p
                return
    else:
        # If the user already has it in PATH, better not force it.
        # On macOS with Homebrew, adjust if needed:
        brew_path = '/opt/homebrew/bin/tesseract'
        if os.path.exists(brew_path):
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = brew_path

# =============================================================================
# OCR utilities - ACTUALIZADO CON PyMuPDF
# =============================================================================

def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Light pre-processing to improve OCR:
    - Upscale if the image is small
    - Convert to grayscale
    - Increase contrast
    - Sharpen
    """
    try:
        w, h = img.size
        if max(w, h) < 1500:
            factor = 1500 / max(w, h)
            img = img.resize((int(w * factor), int(h * factor)))
    except Exception:
        pass

    img = img.convert('L')  # grayscale
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)
    return img

def image_to_text(file_path: str) -> str:
    """✅ MANTENIDO: Para procesar imágenes (no PDFs)"""
    try:
        import pytesseract
        img = Image.open(file_path)
        img = _preprocess_image(img)
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, lang='eng', config=config)
        return text
    except Exception as e:
        logger.error(f"[OCR] Error in image_to_text: {e}")
        return ""

def pdf_to_text(file_path: str) -> str:
    """
    ✅ ACTUALIZADO: Extrae texto de PDF usando PyMuPDF
    """
    print(f"🔍 Intentando procesar PDF: {file_path}")
    
    # Primero intentar con PyMuPDF
    text = process_pdf_with_fitz(file_path)
    if text and len(text.strip()) > 10:  # Si tiene contenido significativo
        return text
    
    print("⚠️  PyMuPDF no pudo extraer texto, intentando fallback...")
    
    # Fallback: intentar con pdf2image + Tesseract si está disponible
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        pages = convert_from_path(file_path, dpi=200)
        all_text = []
        for i, page in enumerate(pages):
            page_text = pytesseract.image_to_string(page, lang='eng')
            all_text.append(page_text)
            print(f"🔤 Página {i+1} (OCR): {len(page_text)} caracteres")
        
        return "\n".join(all_text)
        
    except Exception as e:
        print(f"❌ Fallback también falló: {e}")
        return ""

# =============================================================================
# Parsing and extraction utilities - MEJORADOS
# =============================================================================

MONEY_TOKEN = re.compile(
    r'([€$]?\s*[+-]?(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{2})?)'
)

def _money_tokens_in(text: str):
    """Return all money tokens (with decimal) in text in order."""
    return MONEY_TOKEN.findall(text)

def parse_money(s: str) -> float:
    """
    Convert monetary string to float handling European formats.
    """
    if s is None:
        return 0.0
    s = s.strip()
    s = re.sub(r'[^\d.,+-]', '', s)
    if not s:
        return 0.0

    last_dot = s.rfind('.')
    last_com = s.rfind(',')

    if last_dot > last_com:
        dec = '.'
        thou = ','
    else:
        dec = ','
        thou = '.'

    s = s.replace(thou, '')
    s = s.replace(dec, '.')
    s = re.sub(r'(?<!^)[+-]', '', s)

    try:
        return float(s)
    except ValueError:
        return 0.0

def _first_nonempty_lines(text: str, n: int = 3) -> List[str]:
    lines = [l.strip() for l in text.splitlines()]
    return [l for l in lines if l][:n]

def _clean_lines(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines()]
    return [l for l in lines if l]

def extract_date(text: str) -> str:
    """
    Return a date in the format found (dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd).
    If not found, return an empty string.
    """
    date_patterns = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        r'\b(\d{4}-\d{1,2}-\d{1,2})\b',
        r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})\b',
    ]
    
    for pattern in date_patterns:
        m = re.search(pattern, text.lower())
        if m:
            date_str = m.group(1)
            # Try multiple date formats
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except:
                    continue
    return ""

def extract_amounts(text: str) -> Tuple[float, float]:
    """
    ✅ MEJORADO: Extrae Total y VAT de manera más robusta
    """
    lines = _clean_lines(text)

    # --- TOTAL ---
    total = 0.0
    total_patterns = [
        r'(?i)\btotal\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
        r'(?i)\bamount\s+due\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
        r'(?i)\bbalance\s+due\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
        r'(?i)\bgrand\s+total\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
    ]
    
    for pattern in total_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                total = parse_money(matches[-1])
                if total > 0:
                    break
            except:
                continue

    # --- VAT ---
    vat = 0.0
    vat_patterns = [
        r'(?i)\bvat\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
        r'(?i)\btax\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
        r'(?i)\biva\b[^0-9€$]*(?:[€$]?\s*)([0-9.,]+)',
    ]
    
    for pattern in vat_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                candidate = parse_money(matches[-1])
                if 0 < candidate <= total:  # Sanity check
                    vat = candidate
                    break
            except:
                continue

    # Si no se encontró VAT, calcular como 23% del total (para Irlanda)
    if vat == 0.0 and total > 0:
        vat = round(total * 0.23, 2)

    logger.info(f"[PARSE] Total: {total} | VAT: {vat}")
    return total, vat

def extract_supplier(text: str) -> str:
    """
    ✅ MEJORADO: Extrae nombre del proveedor de manera más inteligente
    """
    lines = _clean_lines(text)
    
    # Patrones de exclusion (no son nombres de proveedor)
    exclude_patterns = [
        r'^invoice$', r'^bill$', r'^receipt$', r'^date$', r'^total$',
        r'^vat$', r'^tax$', r'^amount$', r'^page\d+$', r'^\d+[/-]\d+[/-]\d+$',
        r'^tel:', r'^phone:', r'^email:', r'^www\.', r'^http://', r'^https://'
    ]
    
    for line in lines:
        line = line.strip()
        if (len(line) > 3 and 
            any(c.isalpha() for c in line) and
            not any(re.match(pattern, line.lower()) for pattern in exclude_patterns) and
            not line.isdigit() and
            not re.match(r'^\d+[/-]\d+[/-]\d+$', line)):
            return line[:100]  # Limitar longitud
    
    return "Proveedor No Identificado"

# =============================================================================
# Main API - COMPATIBLE CON TU CÓDIGO EXISTENTE
# =============================================================================

def process_invoice(file_path: str) -> dict:
    """
    ✅ MANTIENE COMPATIBILIDAD: Procesa facturas y devuelve el mismo formato
    """
    logger.info(f"[OCR] Processing file: {file_path}")
    
    # Determinar tipo de archivo y extraer texto
    if file_path.lower().endswith('.pdf'):
        text = pdf_to_text(file_path)  # ✅ Usa PyMuPDF ahora
    else:
        text = image_to_text(file_path)

    # Log preview del texto extraído
    preview = (text or '')[:300]
    logger.info(f"[OCR] Extracted text preview: {preview}")

    # Extraer información
    supplier = extract_supplier(text)
    date_str = extract_date(text)
    total, vat = extract_amounts(text)
    
    # Descripción basada en líneas relevantes
    lines = _first_nonempty_lines(text, n=4)
    description = ' | '.join(lines[1:3]) if len(lines) > 1 else 'Factura procesada'

    result = {
        'supplier': supplier,
        'date': date_str,
        'total': f"{total:.2f}",
        'vat': f"{vat:.2f}",
        'description': description
    }

    logger.info(f"[OCR] Final result: {result}")
    return result

# =============================================================================
# Clase adicional para mejor organización (opcional)
# =============================================================================

class OCRProcessor:
    """
    ✅ NUEVO: Clase para procesamiento OCR más organizado
    """
    
    @staticmethod
    def extract_invoice_data(file_path: str) -> dict:
        """
        Extrae datos de facturas usando PyMuPDF (más robusto)
        """
        try:
            # Usar PyMuPDF para extraer texto
            text = ""
            with fitz.open(file_path) as doc:
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text += page.get_text() + "\n"
            
            # Procesar el texto extraído
            supplier = extract_supplier(text)
            date_str = extract_date(text)
            total, vat = extract_amounts(text)
            
            return {
                "supplier": supplier,
                "date": date_str,
                "total": float(total),
                "vat": float(vat),
                "description": text[:500] if text else "Sin descripción"
            }
            
        except Exception as e:
            logger.error(f"Error procesando PDF con OCRProcessor: {e}")
            return {
                "supplier": "Proveedor No Identificado",
                "total": 0.0,
                "vat": 0.0,
                "date": "",
                "description": "Error en procesamiento OCR"
            }

def process_pdf_with_fitz(file_path: str) -> str:
    """
    ✅ NUEVO: Procesa PDF con PyMuPDF de manera robusta
    """
    try:
        # Verificar que el archivo existe y tiene contenido
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("Archivo PDF está vacío")
            
        print(f"📄 Procesando PDF: {file_path} ({file_size} bytes)")
        
        text = ""
        with fitz.open(file_path) as doc:
            print(f"📑 PDF tiene {doc.page_count} páginas")
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                text += page_text + "\n"
                print(f"📝 Página {page_num + 1}: {len(page_text)} caracteres")
        
        return text
        
    except Exception as e:
        print(f"❌ Error en process_pdf_with_fitz: {e}")
        return ""