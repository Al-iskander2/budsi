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
    # URLs CORREGIDAS - COHERENTES CON VIEWS EXISTENTES
    # =========================================================================
    
    # Invoices
    path("invoices/", views.main_invoice_view, name="main_invoice"),
    path("invoices/create/", views.invoice_create, name="invoice_create"),
    path("invoices/save/", views.invoice_save, name="invoice_save"), 
    path("invoice/list/", views.invoice_list_view, name="invoice_list"),
    path("invoice/upload/", views.invoice_upload_view, name="invoice_upload"),
    path("invoices/<int:invoice_id>/preview/", views.invoice_preview_view, name="invoice_preview"),
    path("invoices/gallery/<int:invoice_id>/", views.invoice_gallery_view, name="invoice_gallery"),
    path("invoice/generate/", views.create_invoice_pdf_view, name="generate_invoice"),

    # Expenses - CORREGIDAS para usar vistas existentes
    path("expenses/", views.tax_view, name="expense_list"),  # ✅ USA VISTA EXISTENTE
    path("expenses/upload/", views.invoice_upload_view, name="expense_upload"),  # ✅ USA VISTA EXISTENTE

    # Projects
    path("project/create/", views.create_project_view, name="create_project_view"),

    # Reports
    path("tax/report/", views.budsi_tax_report, name="tax_report"),
    path("budsi/report/", views.budsi_tax_report, name="budsi_tax_report"),

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
    path("dash/tax/", views.tax_view, name="dash_tax"),
    path("dash/doc/", views.legal_templates_view, name="dash_doc"),
    path("dash/nest/", views.nest_view, name="dash_nest"),
    path("dash/whiz/", views.whiz_view, name="dash_whiz"),
    path("dash/help/", views.help_view, name="dash_help"),

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