import re
import time
from django.db import IntegrityError
from django.utils.text import slugify
from budsi_database.models import Contact

def get_or_create_contact(*, user, name, is_supplier=False, is_client=True, email=None, tax_id=None):
    """Servicio unificado para crear/obtener contactos"""
    if not name or not name.strip():
        name = "Unknown Contact"
    
    name = name.strip()
    
    # Usar tax_id proporcionado o generar uno temporal
    if not tax_id:
        base_tax_id = f"temp-{slugify(name)}-{user.id}"
        tax_id = base_tax_id
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            contact, created = Contact.objects.get_or_create(
                user=user,
                tax_id=tax_id,
                defaults={
                    "name": name,
                    "is_supplier": is_supplier,
                    "is_client": is_client,
                    "email": email or ""
                }
            )
            return contact
            
        except IntegrityError:
            if attempt < max_retries - 1:
                # Intentar con timestamp diferente
                tax_id = f"{base_tax_id}-{int(time.time() * 1000) + attempt}"
                continue
            else:
                # Último intento
                tax_id = f"{base_tax_id}-{int(time.time() * 1000)}-final"
                contact = Contact.objects.create(
                    user=user,
                    name=name,
                    tax_id=tax_id,
                    is_supplier=is_supplier,
                    is_client=is_client,
                    email=email or ""
                )
                return contact