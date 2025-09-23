from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, FiscalProfile, Contact, Invoice, InvoiceLine, TaxPeriod, FiscalConfig

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ('email', 'plan', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'plan')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'plan', 'is_staff', 'is_active')}
        ),
    )

@admin.register(FiscalProfile)
class FiscalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vat_registered', 'vat_number', 'currency')
    search_fields = ('user__email', 'vat_number')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_client', 'is_supplier', 'is_favorite', 'tax_id', 'email')
    list_filter = ('is_client', 'is_supplier', 'is_favorite')
    search_fields = ('name', 'tax_id', 'email', 'user__email')

class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'invoice_type', 'contact', 'date', 'total', 'currency', 'status', 'category')
    list_filter = ('invoice_type', 'status', 'currency', 'date')
    search_fields = ('invoice_number', 'contact__name', 'contact__tax_id', 'user__email', 'category')
    inlines = [InvoiceLineInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'invoice_type', 'contact', 'invoice_number', 'date', 'description', 'category')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'vat_amount', 'total', 'currency')
        }),
        ('Status & Files', {
            'fields': ('status', 'ocr_data', 'original_file')
        }),
    )

@admin.register(TaxPeriod)
class TaxPeriodAdmin(admin.ModelAdmin):
    list_display = ('user', 'period_type', 'start_date', 'end_date', 'status')
    list_filter = ('period_type', 'status')
    date_hierarchy = 'start_date'

@admin.register(FiscalConfig)
class FiscalConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'year')
    list_filter = ('year',)
    search_fields = ('user__email',)
