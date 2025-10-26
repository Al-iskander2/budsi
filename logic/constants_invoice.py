from django.db import models
from decimal import Decimal

class InvoiceType(models.TextChoices):
    SALE = 'sale', 'Sale'
    PURCHASE = 'purchase', 'Purchase'
    CREDIT_NOTE = 'credit_note', 'Credit Note'

DEFAULT_VAT_RATE = Decimal('0.23')
MAX_UPLOAD_SIZE_MB = 10