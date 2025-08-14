###################
# librerias
#################

# ---- 1. Biblioteca estándar ----
import json
import datetime

# ---- 2. Terceras partes ----
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import stripe

# ---- 3. Código local de la aplicación ----
from .forms import CustomUserCreationForm
from .models import FiscalProfile
from logic.debugger import check_template_exists, debug
from logic.fill_pdf import generate_invoice_pdf
from logic.plan_tiers import PLAN_TIERS, require_plan
from logic import stripe as stripe_logic

# ---- 4. NUEVO: OCR + CSV reutilizando tu código existente ----
# Estos módulos vienen de tu fiscal_funcional: ocr_processor, data_manager
from logic.ocr_processor import process_invoice       # devuelve dict: supplier, date, total, vat, description
from logic.data_manager import save_invoice              # guarda en CSV si quieres (opcional)

# ---- 5. NUEVO: modelos y formulario de facturas ----
from .models import Invoice, Client
try:
    # Si ya tienes este form creado (como te lo propuse)
    from .forms import InvoiceForm
except Exception:
    # Fallback: por si aún no lo has creado; no rompe import.
    InvoiceForm = None


######################################
def login_view(request):
    debug("Accessing login_view")
    check_template_exists("budgidesk_app/login.html")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            debug("User authenticated successfully")
            return redirect("dashboard")
        else:
            debug("Authentication failed")
            return render(request, "budgidesk_app/login.html", {"error": "Invalid username or password"})
    return render(request, "budgidesk_app/login.html")


def register_view(request):
    debug("Accessing register_view")
    check_template_exists("budgidesk_app/register.html")
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            debug("User registered successfully")
            login(request, user)
            return redirect('onboarding')
        else:
            debug("Registration form invalid")
    else:
        form = CustomUserCreationForm()
    return render(request, 'budgidesk_app/register.html', {'form': form})


@login_required
def invoice_create_view(request):
    try:
        profile = FiscalProfile.objects.get(user=request.user)
    except FiscalProfile.DoesNotExist:
        return redirect('onboarding')

    if request.method == 'POST':
        profile.invoice_count += 1
        profile.save()

        if request.user.plan == 'lite' and profile.invoice_count > 5:
            return redirect('pricing')

        return render(request, "budgidesk_app/dash/invoice/invoice_created.html", {
            'profile': profile
        })

    return render(request, "budgidesk_app/dash/invoice/invoice_create.html", {
        'invoice_count': profile.invoice_count
    })
 


@require_plan('smart')
@login_required
def invoice_list_view(request):
    debug("Accessing invoice_list_view")
    check_template_exists("budgidesk_app/invoices/invoice_list.html")
    return render(request, "budgidesk_app/invoices/invoice_list.html")


@require_plan('smart')
@login_required
def tax_report_view(request):
    debug("Accessing tax_report_view")
    check_template_exists("budgidesk_app/taxes/tax_report.html")
    return render(request, "budgidesk_app/taxes/tax_report.html")


@require_plan('smart')
@login_required
def balance_overview_view(request):
    debug("Accessing balance_overview_view")
    check_template_exists("budgidesk_app/finances/balance_overview.html")
    return render(request, "budgidesk_app/finances/balance_overview.html")


@login_required
def account_settings_view(request):
    debug("Accessing account_settings_view")
    check_template_exists("budgidesk_app/account_settings.html")
    return render(request, "budgidesk_app/account_settings.html")


@require_plan('elite')
@login_required
def legal_templates_view(request):
    debug("Accessing legal_templates_view")
    check_template_exists("budgidesk_app/legal_templates.html")
    return render(request, "budgidesk_app/legal_templates.html")


@login_required
def reminders_view(request):
    debug("Accessing reminders_view")
    check_template_exists("budgidesk_app/reminders.html")
    return render(request, "budgidesk_app/reminders.html")


def intro_view(request):
    debug("Accessing intro_view")
    check_template_exists("budgidesk_app/intro.html")
    return render(request, "budgidesk_app/intro.html")

@login_required
def onboarding_view(request):
    debug("Accessing onboarding_view")
    check_template_exists("budgidesk_app/onboard.html")
    if request.method == "POST":
        # ← Todas estas líneas deben ir indentadas dentro del `if`
        FiscalProfile.objects.create(
            user=request.user,
            full_name        = request.POST.get("full_name"),
            email            = request.POST.get("email"),
            phone            = request.POST.get("phone"),
            logo             = request.FILES.get("logo"),
            business_name    = request.POST.get("business_name"),
            profession       = request.POST.get("profession"),
            sector           = request.POST.get("sector"),
            currency         = request.POST.get("currency"),
            invoice_defaults = request.POST.get("invoice_defaults"),
            payment_terms    = request.POST.get("payment_terms"),
            late_notice      = request.POST.get("late_notice"),
            payment_methods  = request.POST.get("payment_methods"),
            vat_registered   = (request.POST.get("vat_registered") == "yes"),
            vat_number       = request.POST.get("vat_number", ''),
            pps_number       = request.POST.get("pps_number", ''),
            iban             = request.POST.get("iban", ''),
        )
        return redirect("dashboard")
    # ← Este `return` queda al mismo nivel que el `if`
    return render(request, "budgidesk_app/onboard.html")




@csrf_exempt
@login_required
def process_payment_view(request):
    debug("Accessing process_payment_view")
    if request.method == "POST":
        plan_code = request.GET.get("plan", "smart_monthly")
        user = request.user
        if "elite" in plan_code:
            user.plan = "elite"
        elif "smart" in plan_code:
            user.plan = "smart"
        else:
            user.plan = "lite"
        user.save()
        debug(f"Plan actualizado para {user.username}: {user.plan}")
        return redirect("dashboard")
    return redirect("checkout")


@login_required
def pricing_view(request):
    debug("Accessing pricing_view")
    check_template_exists("budgidesk_app/pricing.html")
    return render(request, "budgidesk_app/pricing.html")


@login_required
def dashboard_view(request):
    debug("Accessing dashboard_view")
    check_template_exists("budgidesk_app/dashboard.html")
    return render(request, "budgidesk_app/dashboard.html")


# 🔽 Nuevas vistas para las secciones movidas al subdirectorio "dash"

@login_required
def flow_view(request):
    return render(request, "budgidesk_app/dash/flow/flow.html")

@login_required
def pulse_view(request):
    return render(request, "budgidesk_app/dash/pulse/pulse.html")

@login_required
def buzz_view(request):
    return render(request, "budgidesk_app/dash/buzz/buzz.html")

@login_required
def track_view(request):
    return render(request, "budgidesk_app/dash/track/track.html")

@login_required
def tax_view(request):
    return render(request, "budgidesk_app/dash/tax/tax_report.html")

@login_required
def doc_view(request):
    return render(request, "budgidesk_app/dash/doc/legal_templates.html")

@login_required
def nest_view(request):
    return render(request, "budgidesk_app/dash/nest/nest.html")

@login_required
def whiz_view(request):
    return render(request, "budgidesk_app/dash/whiz/whiz.html")

@login_required
def help_view(request):
    return render(request, "budgidesk_app/dash/help_support/support.html")


@login_required
def create_invoice_pdf_view(request):
    profile = FiscalProfile.objects.get(user=request.user)
    pdf_path = generate_invoice_pdf(profile)
    return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename="invoice.pdf")

# Funciones para los pago tipo stripe     

# Cambio de estatus en el plan 
stripe.api_key = settings.STRIPE_SECRET_KEY 
@csrf_exempt
@login_required
def create_payment_intent_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    data = json.loads(request.body)
    amount = data.get("amount", 0)
    plan_code = data.get("plan_code")

    try:
        # 1) Crear el intento de pago
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="eur",
            metadata={
                "plan_code": plan_code,
                "user_id": request.user.id
            }
        )

        # 2) Actualizar el plan del usuario según lo pagado
        if plan_code and isinstance(plan_code, str):
            if plan_code.startswith("smart"):
                request.user.plan = "smart"
            elif plan_code.startswith("elite"):
                request.user.plan = "elite"
            else:
                request.user.plan = "lite"
            request.user.save()

        return JsonResponse({"clientSecret": intent.client_secret})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



@login_required
def payment_page(request):
    plan_code = request.GET.get("plan", "smart_monthly")
    plan_map = {
        "smart_monthly": {"name": "Budsi Smart", "amount": 12.99, "interval": "month"},
        "smart_yearly": {"name": "Budsi Smart", "amount": 129, "interval": "year"},
        "elite_monthly": {"name": "Budsi Elite", "amount": 17.99, "interval": "month"},
        "elite_yearly": {"name": "Budsi Elite", "amount": 179, "interval": "year"},
    }
    plan_info = plan_map.get(plan_code)

    if not plan_info:
        return redirect("pricing")  # fallback

    return render(request, "budgidesk_app/payment.html", {
        "plan_code": plan_code,
        "name": plan_info["name"],
        "amount": plan_info["amount"],
        "interval": plan_info["interval"],
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    })


# =====================================================================
#                    ⬇⬇⬇  NUEVO: Upload → OCR → Preview  ⬇⬇⬇
# =====================================================================

def _parse_date_str(date_str: str):
    """
    Intenta parsear 'dd/mm/yyyy', 'dd-mm-yyyy' o 'yyyy-mm-dd' a date.
    Devuelve None si no se logra.
    """
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except Exception:
            pass
    return None


@login_required
def invoice_upload_view(request):
    """
    Recibe archivo 'file', ejecuta OCR con tu ocr_processor.process_invoice,
    crea un borrador de Invoice (type='in'), y redirige al preview para editar.
    """
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]

        # 1) Crear invoice mínima para guardar el archivo
        invoice = Invoice.objects.create(
            user=request.user,
            type="in",                      # recibida/compra
            date=timezone.now().date(),
            amount=0,
            vat=0,
            description="",
            original_file=f,               # Django guarda físicamente
            ocr_data={},
            is_confirmed=False,
        )

        # 2) Ejecutar OCR usando TU módulo
        file_path = invoice.original_file.path
        debug(f"OCR on: {file_path}")
        ocr = process_invoice(file_path) or {}

        # 3) Mapear a campos del modelo
        #    ocr keys: supplier, date, total, vat, description
        supplier_name = (ocr.get("supplier") or "").strip() or "Supplier"
        parsed_date = _parse_date_str(ocr.get("date") or "")
        try:
            amount = float(ocr.get("total") or 0)
        except Exception:
            amount = 0.0
        try:
            vat = float(ocr.get("vat") or 0)
        except Exception:
            vat = 0.0
        description = (ocr.get("description") or "").strip()

        # 4) Vincular/crear supplier como Client
        client, _ = Client.objects.get_or_create(
            user=request.user,
            name=supplier_name,
            defaults={"is_supplier": True}
        )

        # 5) Guardar borrador con datos extraídos
        invoice.client = client
        if parsed_date:
            invoice.date = parsed_date
        invoice.amount = amount
        invoice.vat = vat
        invoice.description = description or "OCR placeholder: review and correct."
        invoice.ocr_data = ocr
        invoice.save()

        # (Opcional) Guardar también a CSV “purchases” de tu módulo existente
        try:
            save_invoice(
                {"supplier": supplier_name, "date": ocr.get("date") or "", "total": amount, "description": description},
                invoice_type="purchase",
                prevent_duplicates=True
            )
        except Exception as e:
            debug(f"CSV save skipped: {e}")

        # 6) Redirigir a preview para editar/corregir
        return redirect("invoice_preview", invoice_id=invoice.id)

    # GET o sin archivo → vuelve al módulo TAX (tu pantalla actual)
    return redirect("dash_tax")


@login_required
def invoice_preview_view(request, invoice_id: int):
    """
    Muestra 'preview.html' con el documento original (img/pdf) y form editable.
    Al confirmar, marca is_confirmed=True y vuelve a la lista de invoices.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    # Asegurar template (si usas debugger)
    try:
        check_template_exists("budgidesk_app/invoices/preview.html")
    except Exception:
        pass

    if request.method == "POST" and InvoiceForm is not None:
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        if form.is_valid():
            inv = form.save(commit=False)
            if "confirm" in request.POST:
                inv.is_confirmed = True
            inv.save()

            # (Opcional) si confirmas una recibida, regraba CSV “purchases”
            try:
                save_invoice(
                    {
                        "supplier": inv.client.name if inv.client else "",
                        "date": inv.date.strftime("%Y-%m-%d"),
                        "total": float(inv.amount or 0),
                        "description": inv.description or "",
                    },
                    invoice_type="purchase",
                    prevent_duplicates=True
                )
            except Exception as e:
                debug(f"CSV save on confirm skipped: {e}")

            return redirect("invoice_list")
    else:
        form = InvoiceForm(instance=invoice, user=request.user) if InvoiceForm else None

    original_url = invoice.original_file.url if invoice.original_file else None
    is_pdf = (original_url or "").lower().endswith(".pdf")

    return render(request, "budgidesk_app/invoices/preview.html", {
        "invoice": invoice,
        "form": form,
        "original_url": original_url,
        "is_pdf": is_pdf,
    })
