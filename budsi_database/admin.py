from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FiscalProfile, Contact, Invoice, InvoiceLine, TaxPeriod, FiscalConfig, Project

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'plan', 'is_staff', 'is_active')
    list_filter = ('plan', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'fiscal_data', 'business_data')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Plan', {'fields': ('plan',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'plan', 'is_staff', 'is_active'),
        }),
    )

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'start_date', 'end_date', 'is_active')
    list_filter = ('status', 'is_active', 'start_date')
    search_fields = ('name', 'description', 'user__email')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'description')}),
        ('Status', {'fields': ('status', 'is_active')}),
        ('Dates', {'fields': ('start_date', 'end_date')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

@admin.register(FiscalProfile)
class FiscalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'legal_name', 'business_name', 'vat_number', 'tax_country', 'vat_registered')
    list_filter = ('tax_country', 'vat_registered', 'period_type', 'accounting_method')
    search_fields = ('user__email', 'legal_name', 'business_name', 'vat_number', 'pps_number')
    
    fieldsets = (
        ('Business Identity', {'fields': ('user', 'legal_name', 'business_name', 'business_type', 'profession', 'sector')}),
        ('Contact Information', {'fields': ('contact_full_name', 'phone', 'logo')}),
        ('Tax Information', {'fields': ('vat_registered', 'vat_number', 'pps_number', 'tax_country', 'tax_region')}),
        ('Business Address', {'fields': ('addr_line1', 'addr_line2', 'city', 'county', 'eircode', 'country')}),
        ('Invoicing Settings', {'fields': ('currency', 'payment_terms', 'invoice_defaults', 'payment_methods', 'accounting_method')}),
        ('Period Configuration', {'fields': ('period_type', 'fiscal_year_start')}),
        ('Banking Information', {'fields': ('iban', 'bic', 'invoice_footer')}),
        ('OCR Settings', {'fields': ('auto_detect_contacts', 'ocr_confidence_threshold')}),
    )

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'tax_id', 'email', 'is_supplier', 'is_client', 'is_favorite')
    list_filter = ('is_supplier', 'is_client', 'is_favorite')
    search_fields = ('name', 'tax_id', 'email', 'user__email')
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'tax_id', 'email')}),
        ('Contact Type', {'fields': ('is_supplier', 'is_client', 'is_favorite')}),
    )

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'contact', 'date', 'total', 'currency', 'status', 'invoice_type', 'is_confirmed')
    list_filter = ('status', 'invoice_type', 'currency', 'date', 'is_confirmed')
    search_fields = ('invoice_number', 'contact__name', 'user__email', 'description')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {'fields': ('user', 'invoice_type', 'contact', 'invoice_number', 'date')}),
        ('Financial Details', {'fields': ('subtotal', 'vat_amount', 'total', 'currency')}),
        ('Additional Information', {'fields': ('description', 'category', 'project', 'status', 'is_confirmed')}),
        ('Files and Data', {'fields': ('ocr_data', 'original_file')}),
        ('System Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price', 'vat_rate', 'line_total')
    list_filter = ('vat_rate',)
    search_fields = ('description', 'invoice__invoice_number')
    
    def line_total(self, obj):
        return obj.quantity * obj.unit_price
    line_total.short_description = 'Line Total'

@admin.register(TaxPeriod)
class TaxPeriodAdmin(admin.ModelAdmin):
    list_display = ('user', 'period_type', 'start_date', 'end_date', 'status')
    list_filter = ('period_type', 'status')
    search_fields = ('user__email',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Period Information', {'fields': ('user', 'period_type', 'start_date', 'end_date')}),
        ('Status and Data', {'fields': ('status', 'tax_data')}),
    )

@admin.register(FiscalConfig)
class FiscalConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'year')
    list_filter = ('year',)
    search_fields = ('user__email',)
    
    fieldsets = (
        ('Configuration', {'fields': ('user', 'year', 'config')}),
    )

# Configuración del sitio de administración
admin.site.site_header = 'Budsi Administration'
admin.site.site_title = 'Budsi Admin'
admin.site.index_title = 'Welcome to Budsi Administration'