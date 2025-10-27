import tempfile
import os
from decimal import Decimal
from datetime import datetime
from django.db import transaction

from budsi_database.models import Invoice, FiscalProfile
from logic.create_contact import get_or_create_contact
from logic.ocr_processor import InvoiceOCR

class InvoiceService:
    """Servicio para manejar operaciones de facturas"""
    
    @staticmethod
    def create_expense_from_ocr(user, file) -> Invoice:
        """Crea una factura de gasto desde OCR"""
        print(f"🔄 InvoiceService.create_expense_from_ocr iniciado")
        
        try:
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            print(f"📁 Archivo temporal creado: {tmp_path}")
            
            try:
                # Procesar OCR
                print("🔍 Llamando a InvoiceOCR.process_invoice...")
                ocr_data = InvoiceOCR.process_invoice(tmp_path)
                
                print(f"📊 Datos OCR recibidos: {ocr_data}")
                
                # Validar datos extraídos
                if ocr_data['confidence'] == 'low':
                    print(f"⚠️ ADVERTENCIA: OCR de baja confianza")
                
                supplier_name = ocr_data['supplier']
                total = Decimal(ocr_data['total'])
                vat = Decimal(ocr_data['vat'])
                
                print(f"💰 Montos procesados - Total: {total}, VAT: {vat}")
                
                if total == 0:
                    print("⚠️ ADVERTENCIA: Monto total es 0")
                
                # Crear contacto
                print(f"👥 Creando contacto para: {supplier_name}")
                contact = get_or_create_contact(
                    user=user,
                    name=supplier_name,
                    is_supplier=True,
                    is_client=False
                )
                print(f"✅ Contacto creado/obtenido: {contact.id} - {contact.name}")
                
                # Calcular subtotal
                subtotal = total - vat
                print(f"🧮 Subtotal calculado: {subtotal}")
                
                # ✅ CORREGIR: Crear invoice PRIMERO sin archivo
                print("📝 Creando objeto Invoice...")
                invoice = Invoice.objects.create(
                    user=user,
                    contact=contact,
                    invoice_type="purchase",
                    date=ocr_data['date'] or datetime.now().date(),
                    subtotal=subtotal,
                    vat_amount=vat,
                    total=total,
                    description=ocr_data['description'],
                    ocr_data=ocr_data,
                    is_confirmed=False,
                )
                
                # ✅ CORREGIR: Ahora guardar el archivo original
                print(f"📁 Guardando archivo original: {file.name}")
                invoice.original_file.save(file.name, file)
                invoice.save()  # Guardar cambios
                
                print(f"✅ INVOICE CREADO EXITOSAMENTE: {invoice.id}")
                print(f"📋 Detalles: {supplier_name} - €{total} - {invoice.date}")
                print(f"📁 Archivo guardado: {invoice.original_file.name}")
                
                return invoice
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    print("🧹 Archivo temporal eliminado")
                    
        except Exception as e:
            print(f"❌ ERROR en create_expense_from_ocr: {str(e)}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            raise

    @staticmethod
    def create_sale_invoice(user, form_data) -> Invoice:
        """Crea factura de venta manual"""
        print(f"🔄 InvoiceService.create_sale_invoice iniciado")
        print(f"👤 Usuario: {user.id}")
        print(f"📋 Datos del formulario: {form_data}")
        
        try:
            profile = FiscalProfile.objects.get(user=user)
            print(f"📊 Perfil fiscal encontrado: {profile.business_name}")
            
            with transaction.atomic():
                # Generar número de factura
                invoice_count = profile.invoice_count + 1
                invoice_number = f"INV-{invoice_count:06d}"
                print(f"🔢 Número de factura generado: {invoice_number}")
                
                # Crear contacto
                contact_name = form_data.get("contact", "").strip()
                print(f"👥 Creando contacto para: {contact_name}")
                contact = get_or_create_contact(
                    user=user,
                    name=contact_name,
                    is_supplier=False,
                    is_client=True
                )
                print(f"✅ Contacto creado: {contact.id}")
                
                # Procesar montos
                subtotal = Decimal(form_data.get("subtotal", 0))
                vat_amount = Decimal(form_data.get("vat_amount", 0))
                total = subtotal + vat_amount
                print(f"💰 Montos - Subtotal: {subtotal}, VAT: {vat_amount}, Total: {total}")
                
                # Crear factura
                print("📝 Creando factura de venta...")
                invoice = Invoice.objects.create(
                    user=user,
                    contact=contact,
                    invoice_type="sale",
                    invoice_number=invoice_number,
                    date=form_data.get("date"),
                    subtotal=subtotal,
                    vat_amount=vat_amount,
                    total=total,
                    description=form_data.get("description", ""),
                    category=form_data.get("category", ""),
                    project=form_data.get("project", ""),
                    is_confirmed=True,
                )
                
                # Actualizar contador
                profile.invoice_count = invoice_count
                profile.save()
                print(f"📊 Contador de facturas actualizado: {invoice_count}")
                
                print(f"✅ FACTURA DE VENTA CREADA: {invoice_number}")
                return invoice
                
        except Exception as e:
            print(f"❌ ERROR en create_sale_invoice: {str(e)}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            raise