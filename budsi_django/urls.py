from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Admin panel - ¡AGREGA ESTA LÍNEA!
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

    # ... (el resto de tus URLs permanecen igual)
    path("invoice/create/", views.invoice_create, name="invoice_create"),
    path("invoice/list/", views.invoice_list_view, name="invoice_list"),
    path("invoice/generate/", views.create_invoice_pdf_view, name="generate_invoice"),
    path("invoice/upload/", views.invoice_upload_view, name="invoice_upload"),
    path("invoices/<int:invoice_id>/preview/", views.invoice_preview_view, name="invoice_preview"),
    path("invoices/create/", views.invoice_create, name="invoice_create_sale"),
    path("tax/report/", views.budsi_tax_report, name="tax_report"),
    path("budsi/report/", views.budsi_tax_report, name="budsi_tax_report"),
    path("account/settings/", views.account_settings_view, name="account_settings"),
    path("legal/templates/", views.legal_templates_view, name="legal_templates"),
    path("reminders/", views.reminders_view, name="reminders"),
    path("process-payment/", views.process_payment_view, name="process_payment"),
    path("pago/", views.payment_page, name="payment_page"),
    path("crear-intento-pago/", views.create_payment_intent_view, name="create-payment-intent"),
    path("pricing/", views.pricing_view, name="pricing"),
    path("dash/flow/", views.flow_view, name="dash_flow"),
    path("dash/pulse/", views.pulse_view, name="dash_pulse"),
    path("dash/buzz/", views.buzz_view, name="dash_buzz"),
    path("dash/track/", views.track_view, name="dash_track"),
    path("dash/tax/", views.tax_view, name="dash_tax"),
    path("dash/doc/", views.legal_templates_view, name="dash_doc"),
    path("dash/nest/", views.nest_view, name="dash_nest"),
    path("dash/whiz/", views.whiz_view, name="dash_whiz"),
    path("dash/help/", views.help_view, name="dash_help"),
    path("invoices/gallery/<int:invoice_id>/", views.invoice_gallery_view, name="invoice_gallery"),
]

# Para servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)