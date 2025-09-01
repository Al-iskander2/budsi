# budgidesk_app/urls.py

from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views


urlpatterns = [
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

    # Invoicing
    path("invoice/create/", views.invoice_create_view, name="invoice_create"),
    path("invoice/list/", views.invoice_list_view, name="invoice_list"),

    # Taxes
    path("tax/report/", views.budsi_tax_report, name="tax_report"),

    # Finances
    path("finances/overview/", views.balance_overview_view, name="balance_overview"),

    # Extras
    path("account/settings/", views.account_settings_view, name="account_settings"),
    path("legal/templates/", views.legal_templates_view, name="legal_templates"),
    path("reminders/", views.reminders_view, name="reminders"),

    # Payments
    path("process-payment/", views.process_payment_view, name="process_payment"),

    # Pricing
    path("pricing/", views.pricing_view, name="pricing"),

    # Dashboard subsections
    path("dash/flow/", views.flow_view, name="dash_flow"),
    path("dash/pulse/", views.pulse_view, name="dash_pulse"),
    path("dash/buzz/", views.buzz_view, name="dash_buzz"),
    path("dash/track/", views.track_view, name="dash_track"),
    path("dash/tax/", views.tax_view, name="dash_tax"),
    path("dash/doc/", views.doc_view, name="dash_doc"),
    path("dash/nest/", views.nest_view, name="dash_nest"),
    path("dash/whiz/", views.whiz_view, name="dash_whiz"),
    path("dash/help/", views.help_view, name="dash_help"),

    # Invoice PDF generation
    path("invoice/generate/", views.create_invoice_pdf_view, name="generate_invoice"),

    # Stripe
    path("pago/", views.payment_page, name="payment_page"),
    path("crear-intento-pago/", views.create_payment_intent_view, name="create-payment-intent"),


    # esto es para invoices de ventas 
    path("invoices/create/", views.invoice_create, name="invoice_create"),
    

    # Upload OCR + Preview
    path("invoice/upload/", views.invoice_upload_view, name="invoice_upload"),
    path("invoices/<int:invoice_id>/preview/", views.invoice_preview_view, name="invoice_preview"),
    path("budsi/report/", views.budsi_tax_report, name="budsi_tax_report"),


    


]
