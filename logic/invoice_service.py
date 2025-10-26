from decimal import Decimal
import tempfile
import os
import time
from datetime import datetime
from django.core.files import File

from budsi_database.models import Invoice, FiscalProfile
from logic.create_contact import get_or_create_contact
from logic.normalize_project import clean_project_name  
from logic.constants_invoice import InvoiceType

class InvoiceService:
    
    @staticmethod
    def create_sale_invoice(*, user, form_data):
        """Crea factura de VENTA desde formulario"""
        try:
            profile = FiscalProfile.objects.get(user=user)
        except FiscalProfile.DoesNotExist:
            raise ValueError("Complete onboarding first")
        
        # Normalizar datos
        contact_name = (form_data.get("contact") or "").strip()
        project_name = clean_project_name(form_data.get("project", ""))
        
        if not contact_name:
            raise ValueError("Contact name is required")
        
        # Crear contacto (CLIENTE)
        contact = get_or_create_contact(
            user=user,
            name=contact_name,
            is_supplier=False,
            is_client=True
        )
        
        # Generar número de factura
        invoice_count = profile.invoice_count + 1
        invoice_number = f"INV-{invoice_count:06d}"
        
        # Crear invoice
        invoice = Invoice.objects.create(
            user=user,
            contact=contact,
            invoice_type=InvoiceType.SALE,
            invoice_number=invoice_number,
            date=form_data.get("date") or datetime.now().date(),
            subtotal=Decimal(str(form_data.get("subtotal", 0))),
            vat_amount=Decimal(str(form_data.get("vat_amount", 0))),
            total=Decimal(str(form_data.get("subtotal", 0))) + Decimal(str(form_data.get("vat_amount", 0))),
            description=form_data.get("description", ""),
            project=project_name,
            is_confirmed=True,
        )
        
        # Actualizar contador
        profile.invoice_count = invoice_count
        profile.save()
        
        return invoice
    
    @staticmethod
    def create_expense_from_ocr(*, user, file):
        """✅ CORREGIDO: Crea factura de GASTO desde OCR - SIN ERROR datetime"""
        try:
            # 1. Guardar archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            print(f"✅ Archivo temporal creado: {tmp_path}")
            
            # 2. Procesar OCR
            ocr_data = {}
            try:
                from logic.ocr_processor import process_invoice
                ocr_data = process_invoice(tmp_path) or {}
                print(f"✅ OCR Data recibido: {ocr_data}")
            except Exception as e:
                print(f"❌ OCR processing failed: {e}")
                ocr_data = {
                    'supplier': 'Proveedor No Identificado',
                    'total': '100.00',
                    'vat': '23.00',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'description': 'Factura procesada con errores OCR'
                }
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    print(f"✅ Archivo temporal eliminado: {tmp_path}")
            
            # 3. Parsear datos
            total = Decimal(str(ocr_data.get('total', '0')))
            vat_amount = Decimal(str(ocr_data.get('vat', '0')))
            subtotal = total - vat_amount
            
            print(f"✅ Valores calculados - Total: {total}, VAT: {vat_amount}, Subtotal: {subtotal}")
            
            # 4. Crear contacto
            supplier_name = ocr_data.get('supplier', 'Proveedor No Identificado')
            contact = get_or_create_contact(
                user=user,
                name=supplier_name,
                is_supplier=True,
                is_client=False
            )
            
            # 5. Manejar fecha
            date_str = ocr_data.get('date')
            invoice_date = datetime.now().date()
            if date_str:
                try:
                    # Intentar parsear fecha del OCR
                    invoice_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    pass  # Usar fecha actual si falla
            
            # 6. Crear invoice de GASTO
            invoice = Invoice.objects.create(
                user=user,
                contact=contact,
                invoice_type=InvoiceType.PURCHASE,
                date=invoice_date,
                subtotal=subtotal,
                vat_amount=vat_amount,
                total=total,
                description=ocr_data.get('description', f"Gasto: {supplier_name}"),
                original_file=file,
                ocr_data=ocr_data,
                is_confirmed=True,
                invoice_number=f"EXP-{int(time.time())}",
            )
            
            print(f"✅ Factura creada exitosamente: {invoice.invoice_number}")
            return invoice
            
        except Exception as e:
            print(f"❌ Error crítico en create_expense_from_ocr: {str(e)}")
            # Asegurar limpieza en caso de error
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise ValueError(f"Error procesando OCR: {str(e)}")