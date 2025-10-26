import re
from unidecode import unidecode

def clean_project_name(raw: str) -> str:
    """Normaliza nombres de proyecto para consistencia"""
    if not raw or not isinstance(raw, str):
        return ''
    
    # 1. Minúsculas y strip
    name = raw.lower().strip()
    
    # 2. Remover acentos y caracteres especiales
    name = unidecode(name)
    
    # 3. Remover caracteres no alfanuméricos (excepto espacios y guiones)
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    
    # 4. Colapsar espacios múltiples
    name = re.sub(r'\s+', ' ', name)
    
    # 5. Capitalizar palabras
    name = name.title()
    
    # 6. Limitar longitud
    return name[:190]