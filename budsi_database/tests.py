from django.test import TestCase
from .models import User, Contact, Invoice
from decimal import Decimal
from datetime import date

class UserModelTest(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email="test@example.com", password="12345")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("12345"))

class InvoiceModelTest(TestCase):
    def test_create_invoice(self):
        user = User.objects.create_user(email="client@example.com", password="pass")
        contact = Contact.objects.create(user=user, name="Cliente 1", is_client=True)
        invoice = Invoice.objects.create(
            user=user,
            contact=contact,
            invoice_number="INV-001",
            date=date.today(),
            subtotal=Decimal("100.00"),
            vat_amount=Decimal("23.00"),
            total=Decimal("123.00"),
        )
        self.assertEqual(invoice.total, Decimal("123.00"))
        self.assertEqual(str(invoice), f"{invoice.invoice_number} - {contact.name} - {invoice.total} {invoice.currency}")
