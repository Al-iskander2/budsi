import re
import os
import platform
from typing import Tuple, List

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path

# =============================================================================
# Tesseract Configuration
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
                pytesseract.pytesseract.tesseract_cmd = p
                return
    else:
        # If the user already has it in PATH, better not force it.
        # On macOS with Homebrew, adjust if needed:
        brew_path = '/opt/homebrew/bin/tesseract'
        if os.path.exists(brew_path):
            pytesseract.pytesseract.tesseract_cmd = brew_path

_maybe_set_tesseract_path()

# =============================================================================
# OCR utilities
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
    img = Image.open(file_path)
    img = _preprocess_image(img)
    # psm 6: assume block of text; oem 3: default LSTM
    config = '--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(img, lang='eng', config=config)
    except Exception as e:
        print(f"[OCR] Error in image_to_text: {e}")
        text = ""
    return text

def pdf_to_text(file_path: str) -> str:
    try:
        pages = convert_from_path(file_path, dpi=300)
    except Exception as e:
        print(f"[OCR] Error converting PDF to images: {e}")
        return ""

    all_text = []
    for i, page in enumerate(pages, start=1):
        try:
            page_img = _preprocess_image(page)
            config = '--oem 3 --psm 6'
            page_text = pytesseract.image_to_string(page_img, lang='eng', config=config)
            print(f"[OCR] Page {i}: {len(page_text)} characters extracted.")
            all_text.append(page_text)
        except Exception as e:
            print(f"[OCR] Error in OCR for page {i}: {e}")
    return "\n".join(all_text)

# =============================================================================
# Parsing and extraction utilities
# =============================================================================

MONEY_TOKEN = re.compile(
    r'([€$]?\s*[+-]?(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{2}))'
)

def _money_tokens_in(text: str):
    """Return all money tokens (with decimal) in text in order."""
    return MONEY_TOKEN.findall(text)

def parse_money(s: str) -> float:
    """
    Convert monetary string to float handling:
    - 10,000.00
    - 100.000.00
    - 2.300,00
    - € 1.234,56
    Rule: the LAST separator ('.' or ',') is the decimal; the others are thousands.
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
    m = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', text)
    if m:
        return m.group(1)
    m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if m:
        return m.group(1)
    return ""

def extract_amounts(text: str) -> Tuple[float, float]:
    """
    Extract Total and VAT robustly:
      - 'Total' per line (avoids 'Subtotal')
      - 'VAT/IVA' per line, avoiding 'VAT No', 'VAT Number', 'Tax ID', etc.
      - Monetary tokens with decimal or symbol.
      - Sanity check: if VAT > Total, try to fix; if not, set VAT=0.
    """
    lines = _clean_lines(text)

    # --- TOTAL ---
    total = 0.0
    total_lines = [ln for ln in lines
                   if re.search(r'(?i)\btotal\b', ln)
                   and not re.search(r'(?i)sub\s*total', ln)]
    for ln in reversed(total_lines):
        toks = _money_tokens_in(ln)
        if toks:
            total = parse_money(toks[-1])
            break

    if total == 0.0:
        m = re.search(
            r'(?is)\btotal\b[^0-9€$+-]*([€$]?\s*[+-]?(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{2}))',
            text
        )
        if m:
            total = parse_money(m.group(1))

    # --- VAT ---
    vat = 0.0
    vat_exclude = re.compile(r'(?i)\b(vat\s*(no|number)|tax\s*id|nif|cif)\b')
    vat_lines = [ln for ln in lines
                 if re.search(r'(?i)\b(vat|iva)\b', ln) and not vat_exclude.search(ln)]

    vat_lines_sorted = sorted(
        vat_lines,
        key=lambda s: 0 if re.search(r'(?i)@\s*\d{1,2}', s) else 1
    )

    for ln in vat_lines_sorted:
        toks = _money_tokens_in(ln)
        if toks:
            candidate = parse_money(toks[-1])
            vat = candidate
            break

    if vat == 0.0 and total > 0:
        vat = round(total * 0.23, 2)

    if total > 0 and vat > total:
        toks_all = [parse_money(t) for t in _money_tokens_in(text)]
        plausibles = [t for t in toks_all if 0 < t <= total]
        if plausibles:
            vat = max(plausibles)
        else:
            vat = 0.0

    print(f"[PARSE] Total: {total} | VAT: {vat}")
    return total, vat

# =============================================================================
# Main API
# =============================================================================

def process_invoice(file_path: str) -> dict:
    """
    Process an invoice image or PDF and return a dictionary with:
      - supplier
      - date
      - total
      - vat
      - description
    Does not return net_amount or vat_amount (calculated later in data_manager for purchases).
    """
    print(f"[OCR] Processing file: {file_path}")
    if file_path.lower().endswith('.pdf'):
        text = pdf_to_text(file_path)
    else:
        text = image_to_text(file_path)

    preview = (text or '')[:300]
    print(f"[OCR] Extracted text (first 300 chars): {preview!r}")

    lines = _first_nonempty_lines(text, n=4)
    supplier = lines[0] if lines else 'Unknown supplier'
    date_str = extract_date(text)
    total, vat = extract_amounts(text)
    description = ' | '.join(lines[1:3]) if len(lines) > 1 else ''

    result = {
        'supplier': supplier,
        'date': date_str,
        'total': f"{total:.2f}",
        'vat': f"{vat:.2f}",
        'description': description
    }

    print(f"[OCR] Processed result: {result}")
    return result
