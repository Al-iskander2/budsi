import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO


def generate_invoice_pdf(profile, output_path="invoice_output.pdf"):
    # Ruta del template base
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(BASE_DIR, "static", "legal_templates_pdf", "basic_template.pdf")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at: {template_path}")

    # Crear overlay en memoria
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    # Estilo general
    c.setFont("Helvetica", 10)

    # Coordenadas ajustadas para alinear con el PDF base
    # Invoice Header
    c.drawString(450, 740, str(profile.invoice_count))  # Invoice Number
    c.drawString(450, 725, datetime.today().strftime('%Y-%m-%d'))  # Date

    # Billed To
    c.drawString(100, 685, profile.full_name or "Client Name")
    c.drawString(100, 670, profile.business_name or "Business Name")
    c.drawString(100, 655, profile.email or "email@example.com")
    c.drawString(100, 640, profile.phone or "123456789")

    # Payment Info
    c.drawString(100, 610, f"IBAN: {profile.iban or 'N/A'}")
    c.drawString(100, 595, f"VAT: {profile.vat_number or 'N/A'}")

    # Table content (one item demo)
    c.drawString(70, 520, "Consulting Services")   # Description
    c.drawString(300, 520, "1")                   # Qty
    c.drawString(370, 520, "€500.00")             # Unit Price
    c.drawString(470, 520, "€500.00")             # Total

    # Totals
    c.setFont("Helvetica-Bold", 10)
    c.drawString(470, 480, "€500.00")  # Subtotal
    c.drawString(470, 460, "€0.00")    # VAT
    c.drawString(470, 440, "€500.00")  # Total

    c.save()
    packet.seek(0)

    # Leer PDFs
    template_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(packet)
    writer = PdfWriter()

    # Combinar primera página
    base_page = template_pdf.pages[0]
    base_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(base_page)

    # Guardar resultado
    full_output_path = os.path.join(BASE_DIR, output_path)
    with open(full_output_path, "wb") as f:
        writer.write(f)

    return full_output_path
