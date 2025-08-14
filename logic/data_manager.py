
import csv
import os
from typing import Dict, List, Optional, Tuple

# Constantes
VAT_RATE = 0.23  # Tasa de IVA fija del 23%

def safe_float(value) -> float:
    """Convierte a float de forma segura; en error devuelve 0.0."""
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if s == "":
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def _read_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _write_row(path: str, fieldnames: List[str], row: Dict[str, object]) -> None:
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_invoice(
    data: Dict[str, object],
    invoice_type: str,
    *,
    prevent_duplicates: bool = True
) -> bool:
    """
    Guarda una factura en CSV (solo el total, sin cálculos).
    
    Parámetros:
      - data: dict con supplier, date, total, description
      - invoice_type: 'purchase' o 'sale'
      - prevent_duplicates: evita duplicados por (supplier, date, total)
    """
    invoice_type = (invoice_type or "").strip().lower()
    if invoice_type not in {"purchase", "sale"}:
        return False

    supplier = (data.get("supplier") or "").strip()
    date_str = (data.get("date") or "").strip()
    description = (data.get("description") or "").strip()
    total = safe_float(data.get("total"))

    if total <= 0:
        return False

    # Estructura común para ambos tipos
    file_path = "purchases.csv" if invoice_type == "purchase" else "invoices.csv"
    fieldnames = ["supplier", "date", "total", "description"]
    row = {
        "supplier": supplier,
        "date": date_str,
        "total": f"{total:.2f}",
        "description": description
    }

    # Detección de duplicados
    if prevent_duplicates:
        existing = _read_csv(file_path)
        key_new = (supplier, date_str, row["total"])
        for r in existing:
            key_old = (
                (r.get("supplier") or ""),
                (r.get("date") or ""),
                (r.get("total") or ""),
            )
            if key_old == key_new:
                return False

    _write_row(file_path, fieldnames, row)
    return True

def load_data(filename: str) -> List[Dict[str, str]]:
    """Lee un CSV y devuelve una lista de dicts."""
    return _read_csv(filename)