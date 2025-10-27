from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Home
    path("", views.intro_view, name="intro"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Onboarding
    path("onboarding/", views.onboarding_view, name="onboarding"),

    # =========================================================================
    # URLs ACTUALIZADAS - ARQUITECTURA SEPARADA SALES/EXPENSES
    # =========================================================================
    
    # ✅ SALES (Facturas de VENTA)
    path("sales/", views.main_invoice_view, name="sales_list"),
    path("sales/create/", views.invoice_create, name="sales_create"),
    path("sales/upload/", views.invoice_upload_view, name="sales_upload"),
    
    # ✅ EXPENSES (Facturas de GASTO) - CORREGIDAS
    path("expenses/", views.expense_list_view, name="expense_list"),
    path("expenses/create/", views.expenses_create_view, name="expenses_create"),
    path("expenses/upload/", views.expenses_upload_view, name="expense_upload"),

    # =========================================================================
    # URLs COMPATIBILIDAD (mantener temporalmente)
    # =========================================================================
    path("invoices/", views.main_invoice_view, name="main_invoice"),
    path("invoices/create/", views.invoice_create, name="invoice_create"),
    path("invoices/save/", views.invoice_save, name="invoice_save"), 
    path("invoice/list/", views.invoice_list_view, name="invoice_list"),
    path("invoice/upload/", views.invoice_upload_view, name="invoice_upload"),
    path("invoices/<int:invoice_id>/preview/", views.invoice_preview_view, name="invoice_preview"),
    path("invoices/gallery/<int:invoice_id>/", views.invoice_gallery_view, name="invoice_gallery"),
    path("invoice/generate/", views.create_invoice_pdf_view, name="generate_invoice"),

    # Projects
    path("project/create/", views.create_project_view, name="create_project_view"),

    # Reports
    path("dash/tax_report/", views.tax_report_view, name="tax_report"),

    # Account & Settings
    path("account/settings/", views.account_settings_view, name="account_settings"),
    path("legal/templates/", views.legal_templates_view, name="legal_templates"),
    path("reminders/", views.reminders_view, name="reminders"),

    # Payments
    path("process-payment/", views.process_payment_view, name="process_payment"),
    path("pago/", views.payment_page, name="payment_page"),
    path("crear-intento-pago/", views.create_payment_intent_view, name="create-payment-intent"),
    path("pricing/", views.pricing_view, name="pricing"),

    # =========================================================================
    # Dashboard Sections
    # =========================================================================
    path("dash/flow/", views.flow_view, name="dash_flow"),
    path("dash/pulse/", views.pulse_view, name="dash_pulse"),
    path("dash/buzz/", views.buzz_view, name="dash_buzz"),
    path("dash/track/", views.track_view, name="dash_track"),
    path("dash/doc/", views.legal_templates_view, name="dash_doc"),
    path("dash/nest/", views.nest_view, name="dash_nest"),
    path("dash/whiz/", views.whiz_view, name="dash_whiz"),
    path("dash/help/", views.help_view, name="dash_help"),

    # =========================================================================
    # HELP & SUPPORT
    # =========================================================================
    path('help/faqs/', views.faqs_view, name='faqs'),
    path('help/support/', views.help_view, name='help_support'),

    # =========================================================================
    # URLs CREDIT NOTES
    # =========================================================================
    path("credit/note/", views.credit_note_create_view, name="credit_note"),
    path("credit/note/save/", views.credit_note_save_view, name="credit_note_save"),
]

# Para servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)