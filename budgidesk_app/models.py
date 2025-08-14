# budgidesk_app/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# =========================
# Auth: Custom User
# =========================

class CustomUserManager(BaseUserManager):
    """
    Custom manager that uses email as the unique identifier instead of username.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
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
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user that removes `username` and uses `email` as the only identifier.
    """
    username = None
    email = models.EmailField(_('email address'), unique=True)
    plan = models.CharField(max_length=20, default='lite')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.email


# =========================
# Fiscal Profile
# =========================

class FiscalProfile(models.Model):
    """
    1:1 fiscal profile linked to the CustomUser.
    """
    user             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name        = models.CharField(max_length=100)
    email            = models.EmailField(default='')
    phone            = models.CharField(max_length=20, blank=True)
    logo             = models.ImageField(upload_to='user_logos/', blank=True, null=True)

    business_name    = models.CharField(max_length=100)
    profession       = models.CharField(max_length=50, blank=True, default='')
    sector           = models.CharField(max_length=50, blank=True, default='')

    currency         = models.CharField(
        max_length=3,
        choices=[('EUR','EUR'),('GBP','GBP'),('USD','USD')],
        default='EUR'
    )
    invoice_defaults = models.CharField(
        max_length=3,
        choices=[('yes','Yes'),('no','No')],
        default='yes',
        blank=True
    )
    payment_terms    = models.CharField(max_length=50, blank=True, default='')
    late_notice      = models.CharField(max_length=255, blank=True, default='')
    payment_methods  = models.CharField(max_length=255, blank=True, default='')

    vat_registered   = models.BooleanField(default=False)
    vat_number       = models.CharField(max_length=20, blank=True)
    pps_number       = models.CharField(max_length=20, blank=True)
    iban             = models.CharField(max_length=34, blank=True)

    invoice_count    = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Fiscal data of {self.user.email}"


# =========================
# Invoicing: Client & Invoice
# =========================

class Client(models.Model):
    """
    Client/Supplier directory. `is_supplier=True` marks suppliers for received invoices.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50, blank=True)   # VAT / tax number (optional)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_supplier = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "name"]),
            models.Index(fields=["user", "is_supplier"]),
        ]
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        base = self.name or "Client"
        return f"{base} ({self.tax_id})" if self.tax_id else base


class Invoice(models.Model):
    """
    Minimal invoice model for both received ('in') and issued ('out') flows.
    """
    INVOICE_TYPES = (
        ('in', 'Received'),   # purchase invoices (supplier)
        ('out', 'Issued'),    # sales invoices (to client)
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=3, choices=INVOICE_TYPES)
    date = models.DateField()

    # Amounts (keep it simple for now: gross & VAT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)   # Gross total
    vat = models.DecimalField(max_digits=10, decimal_places=2)      # VAT amount
    description = models.TextField(blank=True)

    # Files
    original_file = models.FileField(upload_to='invoices/original/', null=True, blank=True)  # uploaded (jpg/pdf) for received
    pdf_file = models.FileField(upload_to='invoices/pdf/', null=True, blank=True)            # generated for issued

    # OCR data
    ocr_data = models.JSONField(default=dict, blank=True)  # raw OCR payload (key-values)

    # Status
    is_confirmed = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "type", "date"]),
            models.Index(fields=["user", "is_confirmed"]),
        ]
        ordering = ["-date", "-id"]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        kind = dict(self.INVOICE_TYPES).get(self.type, self.type)
        return f"Invoice {self.id} • {kind} • {self.date}"
