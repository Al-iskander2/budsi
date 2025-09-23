###################
# libraries
###################

# ---- 1. Standard library ----
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime

# ---- 2. Django ----
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.db import transaction
from django.contrib import messages

# ---- 3. Stripe ----
import stripe

# ---- 4. Forms ----
from .forms import CustomUserCreationForm, InvoiceForm

# ---- 5. Models ----
from budsi_database.models import FiscalProfile, Invoice, Contact

# ---- 6. Helper logic ----
from logic.debugger import debug
from logic.fill_pdf import generate_invoice_pdf
from logic.data_manager import load_data
from logic.tax_calculator import calculate_taxes


#############################
#  AUTHENTICATION
#############################

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "budgidesk_app/login.html", {"error": "Invalid email or password"})
    return render(request, "budgidesk_app/login.html")


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Especifica el backend manualmente
            from django.contrib.auth import login
            user.backend = 'budsi_django.backends.EmailBackend'
            login(request, user)
            return redirect('onboarding')
    else:
        form = CustomUserCreationForm()
    return render(request, 'budgidesk_app/register.html', {'form': form})


#############################
#  DASHBOARD + ONBOARDING
#############################

@login_required
def dashboard_view(request):
    return render(request, "budgidesk_app/dashboard.html")


@login_required
def onboarding_view(request):
    if request.method == "POST":
        FiscalProfile.objects.create(
            user=request.user,
            contact_full_name=request.POST.get("contact_full_name"),
            phone=request.POST.get("phone"),
            logo=request.FILES.get("logo"),
            business_name=request.POST.get("business_name"),
            profession=request.POST.get("profession"),
            sector=request.POST.get("sector"),
            currency=request.POST.get("currency"),
            invoice_defaults=request.POST.get("invoice_defaults"),
            payment_terms=request.POST.get("payment_terms"),
            late_notice=request.POST.get("late_notice"),
            payment_methods=request.POST.get("payment_methods"),
            vat_registered=(request.POST.get("vat_registered") == "yes"),
            vat_number=request.POST.get("vat_number", ''),
            pps_number=request.POST.get("pps_number", ''),
            iban=request.POST.get("iban", ''),
        )
        return redirect("dashboard")
    return render(request, "budgidesk_app/onboard.html")


#############################
#  MANUAL INVOICES
#############################

@login_required
def invoice_create(request):
    if request.method == 'POST':
        contact_name = (request.POST.get("contact") or "").strip()
        date_str = (request.POST.get("date") or "").strip()
        subtotal_str = (request.POST.get("subtotal") or "0").strip()
        vat_str = (request.POST.get("vat_amount") or "0").strip()
        description = (request.POST.get("description") or "").strip()

        errors = []
        inv_date = parse_date(date_str)

        try:
            subtotal = Decimal(subtotal_str)
            vat_amount = Decimal(vat_str)
        except InvalidOperation:
            errors.append("Amount and VAT must be valid numbers.")
            subtotal, vat_amount = Decimal("0"), Decimal("0")

        if not contact_name:
            errors.append("Contact name is required.")
        if not inv_date:
            errors.append("Invalid date.")

        if errors:
            messages.error(request, " ".join(errors))
            return render(request, "budgidesk_app/dash/invoice/invoice_created.html", {
                "errors": errors, "form_data": request.POST
            })

        try:
            profile = FiscalProfile.objects.get(user=request.user)
            with transaction.atomic():
                contact, _ = Contact.objects.get_or_create(
                    user=request.user,
                    name=contact_name,
                    defaults={"is_supplier": False, "is_client": True}
                )
                Invoice.objects.create(
                    user=request.user,
                    contact=contact,
                    invoice_type="sale",
                    date=inv_date,
                    subtotal=subtotal,
                    vat_amount=vat_amount,
                    total=subtotal + vat_amount,
                    description=description,
                    is_confirmed=True,
                )
                profile.invoice_count += 1
                profile.save()
            messages.success(request, "Invoice saved successfully!")
            return redirect("invoice_create")
        except FiscalProfile.DoesNotExist:
            return redirect("onboarding")

    try:
        profile = FiscalProfile.objects.get(user=request.user)
    except FiscalProfile.DoesNotExist:
        return redirect('onboarding')

    invoices = Invoice.objects.filter(user=request.user, invoice_type="sale").order_by('-date')
    return render(request, "budgidesk_app/dash/invoice/invoice_create.html", {
        'invoice_count': profile.invoice_count,
        'invoices': invoices
    })


@login_required
def invoice_preview_view(request, invoice_id: int):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        if form.is_valid():
            inv = form.save(commit=False)
            if "confirm" in request.POST:
                inv.is_confirmed = True
            inv.total = inv.subtotal + inv.vat_amount
            inv.save()
            return redirect("dash_tax")
    else:
        form = InvoiceForm(instance=invoice, user=request.user)

    original_url = invoice.original_file.url if invoice.original_file else None
    is_pdf = (original_url or "").lower().endswith(".pdf")

    return render(request, "budgidesk_app/dash/expenses/preview_purchase.html", {
        "invoice": invoice,
        "form": form,
        "original_url": original_url,
        "is_pdf": is_pdf,
    })


#############################
#  REPORTS
#############################

@login_required
def tax_view(request):
    invoices = (
        Invoice.objects
        .filter(user=request.user, invoice_type="purchase", is_confirmed=True)
        .select_related('contact')
        .order_by('-date', '-id')
    )
    return render(request, "budgidesk_app/dash/expenses/main_expenses.html", {"invoices": invoices})


@login_required
def budsi_tax_report(request):
    invoices = load_data('invoices.csv')
    purchases = load_data('purchases.csv')
    tax_data = calculate_taxes(invoices, purchases)

    def _D(x):
        try: return Decimal(str(x))
        except: return Decimal('0')

    def _q2(x):
        return x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    rows_sales = []
    for i, inv in enumerate(invoices, start=1):
        total = _D(inv.get('total', 0))
        net = (total / Decimal('1.23')) if total else Decimal('0')
        vat = net * Decimal('0.23')
        rows_sales.append({"n": i, "net": _q2(net), "vat": _q2(vat), "total": _q2(total)})

    rows_pur = []
    for i, pur in enumerate(purchases, start=1):
        total = _D(pur.get('total', 0))
        net = (total / Decimal('1.23')) if total else Decimal('0')
        vat = net * Decimal('0.23')
        rows_pur.append({"n": i, "net": _q2(net), "vat": _q2(vat), "total": _q2(total)})

    taxable_income = _D(tax_data['income']['taxable'])
    first_band = min(taxable_income, Decimal('44000'))
    excess = max(taxable_income - Decimal('44000'), Decimal('0'))

    context = {
        "rows_sales": rows_sales,
        "rows_purchases": rows_pur,
        "tax_data": tax_data,
        "first_band_amount": _q2(first_band),
        "first_band_tax": _q2(first_band * Decimal('0.2')),
        "excess_amount": _q2(excess),
        "excess_tax": _q2(excess * Decimal('0.4')),
        "show_excess": taxable_income > Decimal('44000'),
    }
    return render(request, "budgidesk_app/dash/tax/report.html", context)

#############################
#  FINANCES / BALANCE
#############################

@login_required
def balance_overview_view(request):
    """
    Vista para el overview financiero - placeholder temporal
    """
    # Puedes implementar la lógica financiera aquí más adelante
    context = {
        "message": "Financial overview section - under development"
    }
    return render(request, "budgidesk_app/dash/finances/overview.html", context)


#############################
#  EXTRAS DASHBOARD SECTIONS
#############################

@login_required
def account_settings_view(request):
    return render(request, "budgidesk_app/account_settings.html")


def intro_view(request):
    return render(request, "budgidesk_app/intro.html")

@login_required
def reminders_view(request):
    return render(request, "budgidesk_app/reminders.html")

@login_required
def legal_templates_view(request):
    return render(request, "budgidesk_app/dash/doc/legal_templates.html")

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
def nest_view(request):
    return render(request, "budgidesk_app/dash/nest/nest.html")

@login_required
def whiz_view(request):
    return render(request, "budgidesk_app/dash/whiz/whiz.html")

@login_required
def help_view(request):
    return render(request, "budgidesk_app/dash/help_support/support.html")


#############################
#  PDF INVOICE
#############################

@login_required
def create_invoice_pdf_view(request):
    profile = FiscalProfile.objects.get(user=request.user)
    pdf_path = generate_invoice_pdf(profile)
    return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename="invoice.pdf")


#############################
#  STRIPE PAYMENTS / PLANS
#############################

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@login_required
def process_payment_view(request):
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
        return redirect("dashboard")
    return redirect("checkout")

@login_required
def pricing_view(request):
    return render(request, "budgidesk_app/pricing.html")

@csrf_exempt
@login_required
def create_payment_intent_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = json.loads(request.body)
    amount = data.get("amount", 0)
    plan_code = data.get("plan_code")

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="eur",
            metadata={"plan_code": plan_code, "user_id": request.user.id}
        )

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
        "smart_monthly": {"name": "Budsi Smart", "amount": 1299, "interval": "month"},
        "smart_yearly": {"name": "Budsi Smart", "amount": 12900, "interval": "year"},
        "elite_monthly": {"name": "Budsi Elite", "amount": 1799, "interval": "month"},
        "elite_yearly": {"name": "Budsi Elite", "amount": 17900, "interval": "year"},
    }
    plan_info = plan_map.get(plan_code)

    if not plan_info:
        return redirect("pricing")

    return render(request, "budgidesk_app/payment.html", {
        "plan_code": plan_code,
        "name": plan_info["name"],
        "amount": plan_info["amount"],
        "interval": plan_info["interval"],
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    })


#############################
#  OCR → AUTOMATIC INVOICE
#############################

def _parse_date_str(date_str: str):
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except Exception:
            pass
    return None

@login_required
def invoice_upload_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]

        invoice = Invoice.objects.create(
            user=request.user,
            invoice_type="purchase",
            date=datetime.now().date(),
            subtotal=0,
            vat_amount=0,
            total=0,
            description="",
            original_file=f,
            ocr_data={},
            is_confirmed=False,
        )

        from logic.ocr_processor import process_invoice
        from logic.data_manager import save_invoice

        ocr = process_invoice(invoice.original_file.path) or {}

        supplier_name = (ocr.get("supplier") or "").strip() or "Supplier"
        parsed_date = _parse_date_str(ocr.get("date") or "")
        try:
            subtotal = Decimal(str(ocr.get("total") or 0))
        except Exception:
            subtotal = Decimal("0")
        try:
            vat_amount = Decimal(str(ocr.get("vat") or 0))
        except Exception:
            vat_amount = Decimal("0")
        description = (ocr.get("description") or "").strip()

        contact, _ = Contact.objects.get_or_create(
            user=request.user,
            name=supplier_name,
            defaults={"is_supplier": True}
        )

        invoice.contact = contact
        if parsed_date:
            invoice.date = parsed_date
        invoice.subtotal = subtotal
        invoice.vat_amount = vat_amount
        invoice.total = subtotal + vat_amount
        invoice.description = description or "OCR Invoice (please review)."
        invoice.ocr_data = ocr
        invoice.save()

        try:
            save_invoice(
                {
                    "supplier": supplier_name,
                    "date": ocr.get("date") or "",
                    "total": float(subtotal),
                    "description": description,
                },
                invoice_type="purchase",
                prevent_duplicates=True
            )
        except Exception as e:
            debug(f"CSV save skipped: {e}")

        return redirect("invoice_preview", invoice_id=invoice.id)

    return redirect("dash_tax")


#############################
#  INVOICE GALLERY
#############################

@login_required
def invoice_gallery_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    prev_invoice = (
        Invoice.objects.filter(user=request.user, id__lt=invoice.id)
        .order_by("-id")
        .first()
    )
    next_invoice = (
        Invoice.objects.filter(user=request.user, id__gt=invoice.id)
        .order_by("id")
        .first()
    )

    return render(
        request,
        "budgidesk_app/dash/expenses/invoice_gallery.html",
        {
            "invoice": invoice,
            "prev_invoice": prev_invoice,
            "next_invoice": next_invoice,
        },
    )


@login_required
def invoice_list_view(request):
    invoices = Invoice.objects.filter(user=request.user).order_by("-date", "-id")
    return render(
        request,
        "budgidesk_app/dash/expenses/invoice_list.html",
        {"invoices": invoices},
    )
