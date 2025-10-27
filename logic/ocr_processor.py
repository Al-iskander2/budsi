import re
import os
import logging
from typing import Tuple, Dict, List
from decimal import Decimal, InvalidOperation
from datetime import datetime

from logic.ocr_config import configure_ocr
configure_ocr()

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    print("✅ PyMuPDF disponible")
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("❌ PyMuPDF no disponible")

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    TESSERACT_AVAILABLE = True
    print("✅ Tesseract disponible")
except ImportError:
    TESSERACT_AVAILABLE = False
    print("❌ Tesseract no disponible")

class InvoiceOCR:
    """Procesador de facturas robusto para producción"""
    
    # Patrones mejorados para facturas irlandesas
    DATE_PATTERNS = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # 31/12/2023
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',    # 2023-12-31
        r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b',  # 31 Dec 2023
    ]
    
    TOTAL_KEYWORDS = [
        'total', 'amount due', 'balance due', 'grand total', 
        'final total', 'total amount', 'amount payable', 'invoice total'
    ]
    
    VAT_KEYWORDS = ['vat', 'tax', 'iva', 'value added tax', 'v.a.t.']
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extrae texto de PDF usando PyMuPDF (más rápido y confiable)"""
        print(f"📄 Intentando extraer texto de PDF: {file_path}")
        try:
            if not PYMUPDF_AVAILABLE:
                print("❌ PyMuPDF no disponible para extraer PDF")
                return ""
                
            text = ""
            with fitz.open(file_path) as doc:
                print(f"📑 PDF tiene {doc.page_count} páginas")
                for page_num, page in enumerate(doc):
                    page_text = page.get_text()
                    text += page_text + "\n"
                    print(f"📝 Página {page_num + 1}: {len(page_text)} caracteres")
            
            print(f"✅ Texto extraído del PDF: {len(text)} caracteres totales")
            return text
            
        except Exception as e:
            print(f"❌ Error extrayendo texto PDF: {e}")
            return ""

    @staticmethod
    def extract_text_from_image(file_path: str) -> str:
        """Extrae texto de imágenes usando Tesseract"""
        print(f"🖼️ Intentando extraer texto de imagen: {file_path}")
        try:
            if not TESSERACT_AVAILABLE:
                print("❌ Tesseract no disponible para extraer imagen")
                return ""
                
            img = Image.open(file_path)
            print(f"🖼️ Imagen cargada: {img.size} - Modo: {img.mode}")
            
            # Preprocesamiento básico
            img = img.convert('L')  # Escala de grises
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Configuración para facturas
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789€$.,abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ /-'
            text = pytesseract.image_to_string(img, config=config)
            
            print(f"✅ Texto extraído de imagen: {len(text)} caracteres")
            return text
            
        except Exception as e:
            print(f"❌ Error extrayendo texto de imagen: {e}")
            return ""

    @staticmethod
    def smart_amount_extraction(text: str) -> Tuple[Decimal, Decimal]:
        """
        Extracción inteligente de montos con múltiples estrategias
        """
        print("🔍 Iniciando extracción inteligente de montos...")
        text_lower = text.lower()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        total = Decimal('0')
        vat = Decimal('0')
        
        print(f"📊 Analizando {len(lines)} líneas de texto...")
        
        # ESTRATEGIA 1: Buscar por líneas con palabras clave
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Buscar total
            if any(keyword in line_lower for keyword in InvoiceOCR.TOTAL_KEYWORDS):
                print(f"💰 Línea {i} contiene palabra clave de TOTAL: {line}")
                amounts = InvoiceOCR._extract_amounts_from_line(line)
                print(f"💰 Montos encontrados en línea {i}: {amounts}")
                if amounts:
                    total = max(total, max(amounts))
                    print(f"✅ Total actualizado: {total}")
            
            # Buscar VAT
            if any(keyword in line_lower for keyword in InvoiceOCR.VAT_KEYWORDS):
                print(f"🧾 Línea {i} contiene palabra clave de VAT: {line}")
                amounts = InvoiceOCR._extract_amounts_from_line(line)
                print(f"🧾 Montos VAT encontrados en línea {i}: {amounts}")
                if amounts:
                    valid_vat = [amt for amt in amounts if 0 < amt <= total]
                    if valid_vat:
                        vat = max(vat, max(valid_vat))
                        print(f"✅ VAT actualizado: {vat}")
        
        # ESTRATEGIA 2: Si no se encontró total, buscar el número más grande
        if total == 0:
            print("🔍 No se encontró total por palabras clave, buscando todos los montos...")
            all_amounts = []
            for line in lines:
                line_amounts = InvoiceOCR._extract_amounts_from_line(line)
                all_amounts.extend(line_amounts)
            
            print(f"🔍 Todos los montos encontrados en el texto: {all_amounts}")
            if all_amounts:
                # Filtrar montos que parezcan totales (no muy pequeños)
                significant_amounts = [amt for amt in all_amounts if amt > 10]
                print(f"🔍 Montos significativos (>10): {significant_amounts}")
                if significant_amounts:
                    total = max(significant_amounts)
                    print(f"✅ Total por fallback (monto más grande): {total}")
        
        # ESTRATEGIA 3: Calcular VAT si no se encontró
        if vat == 0 and total > 0:
            vat = (total * Decimal('0.23')).quantize(Decimal('0.01'))
            print(f"🧮 VAT calculado automáticamente (23%): {vat}")
        
        print(f"📊 RESULTADO FINAL - Total: {total}, VAT: {vat}")
        return total, vat

    @staticmethod
    def _extract_amounts_from_line(line: str) -> List[Decimal]:
        """Extrae todos los montos monetarios de una línea - CORREGIDO"""
        print(f"🔍 Analizando línea para montos: '{line}'")
        
        # Patrones mejorados para formatos europeos/irlandeses
        patterns = [
            # Formato europeo con puntos como separadores de miles: 10.000,00 o 100.000,00
            r'€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))',  # €10.000,00 o 100.000,00
            # Formato americano con comas como separadores de miles: 10,000.00
            r'€?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))',  # €10,000.00
            # Formato simple con decimales
            r'€?\s*(\d+(?:,\d{2}))',  # €1000,00
            r'€?\s*(\d+(?:\.\d{2}))',  # €1000.00
            # Montos al final de la línea
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2}))\s*€',  # 10.000,00€
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2}))\s*€',  # 10,000.00€
        ]
        
        amounts = []
        for pattern_idx, pattern in enumerate(patterns):
            matches = re.findall(pattern, line)
            if matches:
                print(f"🔍 Patrón {pattern_idx} encontró matches: {matches}")
                for match in matches:
                    try:
                        # DETERMINAR EL FORMATO BASADO EN EL PATRÓN
                        if pattern_idx in [0, 4]:  # Patrones europeos: 10.000,00
                            # FORMATO EUROPEO: quitar puntos de miles, convertir coma decimal a punto
                            clean_num = match.replace('.', '').replace(',', '.')
                            print(f"🔍 Formato europeo detectado: '{match}' -> '{clean_num}'")
                        elif pattern_idx in [1, 5]:  # Patrones americanos: 10,000.00
                            # FORMATO AMERICANO: quitar comas de miles, dejar punto decimal
                            clean_num = match.replace(',', '')
                            print(f"🔍 Formato americano detectado: '{match}' -> '{clean_num}'")
                        else:
                            # Formatos simples - determinar por el contenido
                            if ',' in match and '.' in match:
                                # Tiene ambos - determinar cuál es el decimal
                                if match.rfind(',') > match.rfind('.'):
                                    clean_num = match.replace('.', '').replace(',', '.')  # Europeo
                                else:
                                    clean_num = match.replace(',', '')  # Americano
                            elif ',' in match:
                                # Solo coma - asumir decimal europeo
                                clean_num = match.replace(',', '.')
                            else:
                                # Solo punto - asumir decimal americano
                                clean_num = match
                            print(f"🔍 Formato simple detectado: '{match}' -> '{clean_num}'")
                        
                        amount = Decimal(clean_num)
                        if amount > 0:
                            amounts.append(amount)
                            print(f"✅ Monto extraído: {amount} (de: '{match}')")
                        else:
                            print(f"⚠️ Monto cero ignorado: {amount} (de: '{match}')")
                            
                    except (InvalidOperation, ValueError) as e:
                        print(f"❌ Error convirtiendo monto '{match}': {e}")
                        continue
        
        print(f"📊 Montos extraídos de la línea: {amounts}")
        return amounts

    @staticmethod
    def extract_supplier_name(text: str) -> str:
        """Extrae el nombre del proveedor de manera inteligente"""
        print("🏢 Extrayendo nombre del proveedor...")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Exclusiones comunes
        exclude_words = {'invoice', 'bill', 'receipt', 'date', 'total', 'vat', 'tax', 
                        'page', 'tel', 'phone', 'email', 'www', 'http', 'https'}
        
        for i, line in enumerate(lines[:10]):  # Solo primeras 10 líneas
            clean_line = line.strip()
            print(f"🔍 Línea {i} candidata: '{clean_line}'")
            
            if (len(clean_line) > 2 and 
                not any(word in clean_line.lower() for word in exclude_words) and
                not re.match(r'^\d+[/-]\d+[/-]\d+$', clean_line) and
                not clean_line.isdigit()):
                print(f"✅ Proveedor identificado: '{clean_line}'")
                return clean_line[:100]  # Limitar longitud
        
        print("❌ No se pudo identificar proveedor, usando valor por defecto")
        return "Supplier Not Identified"

    def extract_date(text: str) -> str:
        """Extrae fecha con múltiples formatos - MEJORADO"""
        print("📅 Extrayendo fecha...")
        
        # Patrones adicionales para formatos sin separadores
        additional_patterns = [
            r'\b(\d{2})(\d{2})(\d{4})\b',  # 24032025 -> 24/03/2025
            r'\b(\d{4})(\d{2})(\d{2})\b',  # 20250324 -> 2025/03/24
        ]
        
        all_patterns = InvoiceOCR.DATE_PATTERNS + additional_patterns
        
        for pattern_idx, pattern in enumerate(all_patterns):
            matches = re.findall(pattern, text)
            if matches:
                date_match = matches[0]
                print(f"🔍 Patrón {pattern_idx} encontró fecha: {date_match}")
                
                # Si el patrón tiene grupos (como dd mm yyyy separados)
                if isinstance(date_match, tuple):
                    date_str = ''.join(date_match)
                    # Intentar diferentes combinaciones
                    possible_formats = [
                        "%d%m%Y",  # 24032025
                        "%Y%m%d",  # 20250324
                        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", 
                        "%d/%m/%y", "%d-%m-%y", "%Y/%m/%d",
                        "%d %b %Y", "%d %B %Y"
                    ]
                else:
                    date_str = date_match
                    possible_formats = [
                        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", 
                        "%d/%m/%y", "%d-%m-%y", "%Y/%m/%d",
                        "%d %b %Y", "%d %B %Y", "%d%m%Y", "%Y%m%d"
                    ]
                
                for fmt in possible_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        formatted_date = parsed_date.strftime("%Y-%m-%d")
                        print(f"✅ Fecha parseada: {formatted_date} (formato: {fmt})")
                        return formatted_date
                    except ValueError:
                        continue
        
        print("❌ No se pudo extraer fecha")
        return ""

    @classmethod
    def process_invoice(cls, file_path: str) -> Dict:
        """
        Procesa una factura y devuelve datos estructurados
        """
        print(f"🚀 INICIANDO PROCESAMIENTO OCR: {file_path}")
        
        try:
            # Determinar tipo de archivo y extraer texto
            if file_path.lower().endswith('.pdf'):
                print("📄 Procesando como PDF...")
                text = cls.extract_text_from_pdf(file_path)
            else:
                print("🖼️ Procesando como imagen...")
                text = cls.extract_text_from_image(file_path)
            
            if not text or len(text.strip()) < 10:
                print("❌ No se pudo extraer texto significativo del archivo")
                return cls._get_fallback_result()
            
            print(f"📝 TEXTO EXTRAÍDO (primeros 500 chars):\n{text[:500]}...")
            
            # Extraer información
            print("🔍 Extrayendo información del texto...")
            supplier = cls.extract_supplier_name(text)
            date_str = cls.extract_date(text)
            total, vat = cls.smart_amount_extraction(text)
            
            # Validar resultados
            if total == 0:
                print("⚠️ ADVERTENCIA: No se pudo extraer monto total")
            
            result = {
                'supplier': supplier,
                'date': date_str,
                'total': f"{total:.2f}",
                'vat': f"{vat:.2f}",
                'description': f"Invoice from {supplier}",
                'raw_text_preview': text[:200] + "..." if len(text) > 200 else text,
                'confidence': 'high' if total > 0 else 'low'
            }
            
            print(f"🎉 PROCESAMIENTO COMPLETADO: {result}")
            return result
            
        except Exception as e:
            print(f"💥 ERROR CRÍTICO en process_invoice: {e}")
            return cls._get_fallback_result()

    @staticmethod
    def _get_fallback_result() -> Dict:
        """Resultado por defecto en caso de error"""
        print("🔄 Devolviendo resultado de fallback...")
        return {
            'supplier': 'Supplier Not Identified',
            'date': '',
            'total': '0.00',
            'vat': '0.00',
            'description': 'OCR processing failed',
            'raw_text_preview': '',
            'confidence': 'low'
        }

# Función de compatibilidad (mantener API existente)
def process_invoice(file_path: str) -> dict:
    """Función de compatibilidad con código existente"""
    print(f"🔗 Llamando a process_invoice (compatibilidad) para: {file_path}")
    return InvoiceOCR.process_invoice(file_path)