from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from decimal import Decimal

# -------- Custom User (email as username) --------
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    plan = models.CharField(max_length=20, default='lite')
    fiscal_data = models.JSONField(default=dict, blank=True)
    business_data = models.JSONField(default=dict, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

# Función para subida de logos
def logo_upload_to(instance, filename):
    return f"logos/user_{instance.user_id}/{filename}"

# -------- Fiscal Profile --------
class FiscalProfile(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='fiscal_profile')

    # Identity / Business
    legal_name = models.CharField(max_length=200, blank=True)
    business_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=50, blank=True)      # sole_trader / limited / ...
    profession = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)

    # Contact & Branding
    contact_full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    logo = models.ImageField(upload_to=logo_upload_to, blank=True, null=True)

    # Tax IDs
    vat_registered = models.BooleanField(default=False)
    vat_number = models.CharField(max_length=32, blank=True)
    pps_number = models.CharField(max_length=16, blank=True)
    tax_country = models.CharField(max_length=2, default='IE')       # ISO-3166-1 alpha-2
    tax_region = models.CharField(max_length=50, blank=True)

    # Address
    addr_line1 = models.CharField(max_length=200, blank=True)
    addr_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    eircode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=2, default='IE')

    # Invoicing & VAT
    currency = models.CharField(max_length=3, default='EUR')
    payment_terms = models.CharField(max_length=100, blank=True)
    invoice_defaults = models.BooleanField(default=True)
    late_notice = models.TextField(blank=True)
    payment_methods = models.TextField(blank=True)
    accounting_method = models.CharField(max_length=16, default='invoice')
    vat_schemes = models.JSONField(default=dict, blank=True)

    # Periods & Reminders
    period_type = models.CharField(max_length=10, default='monthly')
    fiscal_year_start = models.DateField(null=True, blank=True)
    reminders_enabled = models.BooleanField(default=True)
    reminder_days_before_due = models.PositiveIntegerField(default=7)

    # Banking & Footer
    iban = models.CharField(max_length=34, blank=True)
    bic = models.CharField(max_length=11, blank=True)
    invoice_footer = models.TextField(blank=True)

    # Ops / OCR
    auto_detect_contacts = models.BooleanField(default=True)
    ocr_confidence_threshold = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.70'))

    # Legacy/advanced knobs
    tax_bands = models.JSONField(default=dict, blank=True)

    # NUEVO: contador de facturas
    invoice_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Fiscal profile of {self.user}'

# -------- Contacts --------
class Contact(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_supplier = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'tax_id'),)
        indexes = [models.Index(fields=['user', 'name'])]

    def __str__(self):
        return self.name

def invoice_upload_to(instance, filename):
    user_id = instance.user_id or 'anon'
    return f'invoices/user_{user_id}/{filename}'

# -------- Invoice --------
class Invoice(models.Model):
    SALE = 'sale'
    PURCHASE = 'purchase'
    INVOICE_TYPES = ((SALE, 'Sale'), (PURCHASE, 'Purchase'))

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='invoices')
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPES, default=SALE)
    contact = models.ForeignKey('Contact', on_delete=models.PROTECT, related_name='invoices')
    invoice_number = models.CharField(max_length=64)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)

    project = models.CharField(max_length=200, blank=True, null=True)

    category = models.CharField(max_length=100, blank=True, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='EUR')

    status = models.CharField(max_length=20, default='draft')
    is_confirmed = models.BooleanField(default=False)  # NUEVO

    ocr_data = models.JSONField(default=dict, blank=True)
    original_file = models.FileField(upload_to=invoice_upload_to, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('user', 'invoice_number'),)
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.invoice_number} - {self.contact.name} - {self.total} {self.currency}'

# -------- Invoice Line --------
class InvoiceLine(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('23.00'))

    def __str__(self):
        return f'{self.description} ({self.quantity} x {self.unit_price})'

# -------- Tax Period --------
class TaxPeriod(models.Model):
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'
    PERIOD_TYPES = ((MONTHLY, 'Monthly'), (QUARTERLY, 'Quarterly'), (YEARLY, 'Yearly'))

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tax_periods')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default=MONTHLY)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='draft')
    tax_data = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'start_date', 'end_date'])]

    def __str__(self):
        return f'{self.user} {self.period_type} {self.start_date}–{self.end_date}'

class FiscalConfig(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='fiscal_configs')
    year = models.PositiveIntegerField()
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (('user', 'year'),)

    def __str__(self):
        return f'Config {self.year} for {self.user}'

# -------- Project Model --------
class Project(models.Model):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    ON_HOLD = 'on_hold'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
        (ON_HOLD, 'On Hold'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        unique_together = (('user', 'name'),)
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'start_date']),
        ]

    def __str__(self):
        return f'{self.name} ({self.status})'
    
    def get_progress(self):
        """Calcular progreso del proyecto basado en facturas asociadas"""
        from django.db.models import Sum
        try:
            project_invoices = Invoice.objects.filter(user=self.user, project=self.name)
            if project_invoices.exists():
                total_invoiced = project_invoices.aggregate(Sum('total'))['total__sum'] or Decimal('0')
                if self.budget > 0:
                    progress = (total_invoiced / self.budget * 100).quantize(Decimal('0.01'))
                    return min(float(progress), 100.0)
            return 0.0
        except:
            return 0.0