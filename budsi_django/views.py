###################
# libraries
###################

# ---- 1. Standard library ----
import time
import json
import re  
import os
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
from django.template.loader import render_to_string, get_template  
from django.db.models import Sum, Q  
from django.utils.text import slugify
from django.db import IntegrityError

# IMPORTS DE SERVICIOS DESDE LOGIC 
from logic.invoice_service import InvoiceService
from logic.create_contact import get_or_create_contact
from logic.normalize_project import clean_project_name
from logic.constants_invoice import InvoiceType, DEFAULT_VAT_RATE, MAX_UPLOAD_SIZE_MB

# ---- 3. Stripe ----
import stripe

# ---- 4. Forms ----
from .forms import CustomUserCreationForm, InvoiceForm

# ---- 5. Models ----
from budsi_database.models import FiscalProfile, Invoice, Contact, Project

# ---- 6. Helper logic ----
from logic.debugger import debug
from logic.fill_pdf import generate_invoice_pdf
from logic.data_manager import load_data
from logic.tax_calculator import calculate_taxes


#############################
#  FUNCIONES AUXILIARES
#############################

# ✅ NOTA: La función _create_or_get_contact ha sido ELIMINADA
# porque ahora usamos la versión mejorada de logic/create_contact.py

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
    """Vista principal del dashboard con datos reales"""
    try:
        # Obtener datos reales de la base de datos
        from datetime import timedelta
        
        # Obtener facturas del usuario
        sales_invoices = Invoice.objects.filter(
            user=request.user, 
            invoice_type="sale", 
            is_confirmed=True
        )
        
        purchase_invoices = Invoice.objects.filter(
            user=request.user, 
            invoice_type="purchase", 
            is_confirmed=True
        )
        
        # Cálculos básicos
        total_income = sales_invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
        total_expenses = purchase_invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
        net_profit = total_income - total_expenses
        
        # Datos para el dashboard
        context = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'invoice_count': sales_invoices.count(),
            'expense_count': purchase_invoices.count(),
            'recent_invoices': sales_invoices.order_by('-date')[:5],
            'recent_expenses': purchase_invoices.order_by('-date')[:5],
        }
        
        return render(request, "budgidesk_app/dashboard.html", context)
        
    except Exception as e:
        print(f"Error en dashboard: {e}")
        # Fallback con datos básicos
        return render(request, "budgidesk_app/dashboard.html", {
            'total_income': 0,
            'total_expenses': 0,
            'net_profit': 0,
            'invoice_count': 0,
            'expense_count': 0,
            'recent_invoices': [],
            'recent_expenses': [],
        })


@login_required
def main_invoice_view(request):
    """Vista principal de facturas con clientes favoritos"""
    try:
        profile = FiscalProfile.objects.get(user=request.user)
    except FiscalProfile.DoesNotExist:
        return redirect("onboarding")

    sales_invoices = Invoice.objects.filter(
        user=request.user, 
        invoice_type="sale"
    ).select_related('contact').order_by("-date")

    # Obtener clientes favoritos
    favorite_customers = Contact.objects.filter(
        user=request.user, 
        is_client=True
    ).order_by("name")

    context = {
        "invoice_count": profile.invoice_count,
        "sales_invoices": sales_invoices,
        "favorite_customers": favorite_customers,
    }
    return render(request, "budgidesk_app/dash/invoice/main_invoice.html", context)


@login_required
def onboarding_view(request):
    if request.method == "POST":
        invoice_defaults = request.POST.get("invoice_defaults", "").lower() in ["true", "yes", "1"]
        vat_registered = request.POST.get("vat_registered", "").lower() in ["true", "yes", "1"]
        vat_number = request.POST.get("vat_number", "").strip() if vat_registered else ""

        try:
            FiscalProfile.objects.create(
                user=request.user,
                contact_full_name=request.POST.get("contact_full_name"),
                phone=request.POST.get("phone"),
                logo=request.FILES.get("logo"),
                business_name=request.POST.get("business_name"),
                profession=request.POST.get("profession"),
                sector=request.POST.get("sector"),
                currency=request.POST.get("currency"),
                invoice_defaults=invoice_defaults,
                payment_terms=request.POST.get("payment_terms"),
                late_notice=request.POST.get("late_notice"),
                payment_methods=request.POST.get("payment_methods"),
                vat_registered=vat_registered,
                vat_number=vat_number,
                pps_number=request.POST.get("pps_number"),
                iban=request.POST.get("iban"),
            )
            return redirect("dashboard")

        except Exception as e:
            print(f"Error in onboarding: {e}")
            return render(request, "budgidesk_app/onboard.html", {"error": str(e)})

    return render(request, "budgidesk_app/onboard.html")

@login_required
def faqs_view(request):
    """Vista para Preguntas Frecuentes (FAQs)"""
    return render(request, "budgidesk_app/dash/help_support/faqs.html")
    
#############################
#  MANUAL INVOICES
#############################

@login_required
def invoice_create(request):
    """✅ ACTUALIZADO: Usa InvoiceService para crear facturas de venta"""
    if request.method == 'POST':
        try:
            # ✅ USAR NUEVO SERVICIO
            invoice = InvoiceService.create_sale_invoice(
                user=request.user,
                form_data=request.POST
            )
            messages.success(request, f"Invoice {invoice.invoice_number} created successfully!")
            return redirect("main_invoice")
            
        except FiscalProfile.DoesNotExist:
            return redirect("onboarding")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return render(request, "budgidesk_app/dash/invoice/create_invoice.html", {
                "errors": [str(e)],
                "form_data": request.POST
            })
    
    try:
        profile = FiscalProfile.objects.get(user=request.user)
    except FiscalProfile.DoesNotExist:
        return redirect('onboarding')

    # OBTENER PROYECTOS EXISTENTES DE LA BASE DE DATOS
    existing_projects = Invoice.objects.filter(
        user=request.user
    ).exclude(project__isnull=True).exclude(project='').values_list('project', flat=True).distinct()

    return render(request, "budgidesk_app/dash/invoice/create_invoice.html", {
        'profile': profile,
        'invoice_count': profile.invoice_count,
        'existing_projects': existing_projects
    })


@login_required
def invoice_save(request):
    """Vista para guardar facturas - redirige a invoice_create"""
    return invoice_create(request)


@login_required
def invoice_preview_view(request, invoice_id: int):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    # ✅ OBTENER PROYECTOS EXISTENTES
    existing_projects = Invoice.objects.filter(
        user=request.user
    ).exclude(project__isnull=True).exclude(project='').values_list('project', flat=True).distinct()

    if request.method == "POST":
        try:
            # ✅ USAR VALORES DIRECTOS del formulario HTML
            subtotal = Decimal(request.POST.get("subtotal", invoice.subtotal))
            vat_amount = Decimal(request.POST.get("vat_amount", invoice.vat_amount))
            category = request.POST.get("category", "")
            project = request.POST.get("project", "")
            
            # ✅ ACTUALIZAR LA FACTURA con los valores del formulario
            invoice.subtotal = subtotal
            invoice.vat_amount = vat_amount
            invoice.total = subtotal + vat_amount
            invoice.description = request.POST.get("description", invoice.description)
            invoice.category = category
            invoice.project = project
            
            if "confirm" in request.POST:
                invoice.is_confirmed = True
            
            invoice.save()
            
            messages.success(request, "Expense confirmed successfully!")
            return redirect("expense_list")
            
        except Exception as e:
            messages.error(request, f"Error updating expense: {str(e)}")
            print(f"❌ ERROR en invoice_preview_view: {str(e)}")

    # Para GET requests, usar formulario normal pero solo para campos no problemáticos
    form = InvoiceForm(instance=invoice, user=request.user)

    original_url = invoice.original_file.url if invoice.original_file else None
    is_pdf = (original_url or "").lower().endswith(".pdf")

    return render(request, "budgidesk_app/dash/expenses/preview_purchase.html", {
        "invoice": invoice,
        "form": form,
        "original_url": original_url,
        "is_pdf": is_pdf,
        "existing_projects": existing_projects
    })

#############################
#  EXPENSES (PURCHASES)
#############################

@login_required
def expense_list_view(request):
    """Listado de gastos - VERSIÓN MEJORADA"""
    expenses = (
        Invoice.objects
        .filter(user=request.user, invoice_type="purchase")
        .select_related("contact")
        .order_by("-date", "-id")
    )
    
    # Calcular métricas
    total_expenses = expenses.aggregate(total=Sum('total'))['total'] or 0
    total_vat = expenses.aggregate(total=Sum('vat_amount'))['total'] or 0
    total_net = expenses.aggregate(total=Sum('subtotal'))['total'] or 0
    
    # Gastos del mes actual
    from datetime import datetime
    current_month = datetime.now().month
    month_expenses = expenses.filter(date__month=current_month).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Promedio por gasto
    avg_expense = total_expenses / len(expenses) if expenses else 0
    
    context = {
        "expenses": expenses,
        "confirmed_count": expenses.filter(is_confirmed=True).count(),
        "pending_count": expenses.filter(is_confirmed=False).count(),
        "total_expenses": total_expenses,
        "total_vat": total_vat,
        "total_net": total_net,
        "month_expenses": month_expenses,
        "avg_expense": avg_expense,
    }
    
    return render(request, "budgidesk_app/dash/expenses/main_expenses.html", context)

@login_required
def expenses_upload_view(request):
    """✅ VERSIÓN CORREGIDA - Con importación de os y manejo mejorado"""
    print(f"🔍 [1/5] expenses_upload_view INICIADA - Method: {request.method}")
    
    if request.method == "POST" and request.FILES.get("file"):
        try:
            file = request.FILES["file"]
            print(f"🔍 [2/5] Archivo recibido: {file.name} ({file.size} bytes)")
            
            # ✅ Validación adicional de tipo de archivo (AHORA FUNCIONA)
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            file_extension = os.path.splitext(file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                error_msg = f"Formato no soportado. Use: {', '.join(allowed_extensions)}"
                print(f"❌ [3/5] {error_msg}")
                return _handle_upload_response(request, error=error_msg, status=400)
            
            print(f"🔄 [3/5] Llamando a InvoiceService.create_expense_from_ocr...")
            invoice = InvoiceService.create_expense_from_ocr(
                user=request.user,
                file=file
            )
            
            print(f"✅ [4/5] OCR PROCESADO EXITOSAMENTE: Invoice {invoice.id} creada")
            print(f"📋 [5/5] Detalles: {invoice.contact.name} - €{invoice.total}")
            
            success_msg = f"Gasto de {invoice.contact.name} procesado correctamente!"
            return _handle_upload_response(request, success=True, invoice=invoice, message=success_msg)
            
        except Exception as e:
            error_msg = f"Error procesando archivo: {str(e)}"
            print(f"❌ ERROR en expenses_upload_view: {error_msg}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            
            return _handle_upload_response(request, error=error_msg, status=400)
    
    print("❌ Método no permitido o sin archivo")
    return _handle_upload_response(request, error="Método no permitido", status=405)




def _handle_upload_response(request, success=False, invoice=None, message="", error="", status=200):
    """✅ FUNCIÓN AUXILIAR: Maneja respuestas consistentes para AJAX y normal"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        print(f"🔗 Respondiendo vía AJAX - Success: {success}")
        if success and invoice:
            return JsonResponse({
                "success": True, 
                "invoice_id": invoice.id,
                "redirect_url": f"/invoices/{invoice.id}/preview/",
                "message": message
            }, status=status)
        else:
            return JsonResponse({"success": False, "error": error}, status=status)
    else:
        # Request normal - usar messages de Django
        print(f"🔗 Redirigiendo normalmente - Success: {success}")
        if success and invoice:
            messages.success(request, message)
            return redirect("invoice_preview", invoice_id=invoice.id)
        else:
            messages.error(request, error)
            return redirect("expense_list")

# También modificar invoice_upload_view de la misma manera
@login_required
def invoice_upload_view(request):
    """✅ CORREGIDO: Redirige al preview después del OCR"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            invoice = InvoiceService.create_expense_from_ocr(
                user=request.user,
                file=request.FILES['file']
            )
            
            messages.success(request, "Factura procesada correctamente!")
            # ✅ REDIRIGIR AL PREVIEW
            return redirect("invoice_preview", invoice_id=invoice.id)
            
        except Exception as e:
            print(f"Error en OCR upload: {e}")
            messages.error(request, f"Error procesando archivo: {str(e)}")
            return redirect("main_invoice")
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


@login_required
def expenses_create_view(request):
    """✅ NUEVA: Vista para crear gastos manualmente"""
    if request.method == "POST":
        try:
            # Por ahora, usar lógica similar a sales pero para gastos
            supplier_name = (request.POST.get("supplier") or "").strip()
            
            if not supplier_name:
                messages.error(request, "Supplier name is required")
                return redirect("expenses_list")
            
            # Crear contacto como PROVEEDOR
            contact = get_or_create_contact(
                user=request.user,
                name=supplier_name,
                is_supplier=True,
                is_client=False
            )
            
            # Crear invoice de GASTO
            invoice = Invoice.objects.create(
                user=request.user,
                contact=contact,
                invoice_type="purchase",
                date=datetime.now().date(),
                subtotal=Decimal(str(request.POST.get("subtotal", 0))),
                vat_amount=Decimal(str(request.POST.get("vat_amount", 0))),
                total=Decimal(str(request.POST.get("subtotal", 0))) + Decimal(str(request.POST.get("vat_amount", 0))),
                description=request.POST.get("description", ""),
                is_confirmed=True,
                invoice_number=f"EXP-MAN-{int(time.time())}",
            )
            
            messages.success(request, f"Gasto {invoice.invoice_number} creado exitosamente!")
            return redirect("expense_list")
            
        except Exception as e:
            messages.error(request, f"Error creando gasto: {str(e)}")
    
    return render(request, "budgidesk_app/dash/expenses/expenses_create.html")


#############################
#  REPORTS
#############################

@login_required
def tax_report_view(request):
    """Reporte de impuestos con datos reales"""
    try:
        sales_invoices = Invoice.objects.filter(
            user=request.user, invoice_type="sale", is_confirmed=True
        )
        purchase_invoices = Invoice.objects.filter(
            user=request.user, invoice_type="purchase", is_confirmed=True
        )

        tax_data = calculate_taxes(sales_invoices, purchase_invoices)

        return render(request, "budgidesk_app/dash/tax_report/tax_report.html", {
            "tax_data": tax_data,
            "invoices": sales_invoices,
            "purchases": purchase_invoices,
            "sales_count": sales_invoices.count(),
            "purchases_count": purchase_invoices.count()
        })
    except Exception as e:
        print(f"Error en tax report: {e}")
        return render(request, "budgidesk_app/dash/tax_report/tax_report.html", {
            "tax_data": {
                'vat': {'collected': 0, 'paid': 0, 'liability': 0},
                'income': {'gross': 0, 'expenses': 0, 'taxable': 0},
                'income_tax': {'gross': 0, 'credits': 0, 'net': 0},
                'usc': {'total': 0, 'breakdown': []},
                'prsi': 0,
                'total_tax': 0
            },
            "invoices": [],
            "purchases": [],
            "sales_count": 0,
            "purchases_count": 0
        })



#############################
#  FINANCES / BALANCE
#############################

@login_required
def balance_overview_view(request):
    context = {
        "message": "Financial overview section - under development"
    }
    return render(request, "budgidesk_app/dash/finances/overview.html", context)


#############################
#  PROJECT TRACKING
#############################

@login_required
def track_view(request):
    """Vista principal del Project Tracker"""
    try:
        # Obtener todos los proyectos del usuario
        projects = Project.objects.filter(user=request.user)
        
        # Obtener facturas para cálculos
        all_invoices = Invoice.objects.filter(user=request.user, is_confirmed=True)
        sales_invoices = all_invoices.filter(invoice_type='sale')
        purchase_invoices = all_invoices.filter(invoice_type='purchase')
        
        # Cálculos globales
        total_earned = sales_invoices.aggregate(Sum('total'))['total__sum'] or Decimal('0')
        total_spent = purchase_invoices.aggregate(Sum('total'))['total__sum'] or Decimal('0')
        net_profit = total_earned - total_spent
        
        context = {
            'projects': projects,
            'total_earned': total_earned,
            'total_spent': total_spent,
            'net_profit': net_profit,
            'active_projects_count': projects.filter(is_active=True).count(),
        }
        
    except Exception as e:
        print(f"Error en track_view: {e}")
        context = {
            'projects': [],
            'total_earned': 0,
            'total_spent': 0,
            'net_profit': 0,
            'active_projects_count': 0,
        }
    
    return render(request, "budgidesk_app/dash/track/track.html", context)


@login_required
def create_project_view(request):
    """✅ ACTUALIZADO: Vista para crear nuevos proyectos con normalización"""
    if request.method == "POST":
        try:
            name = request.POST.get("project_name", "").strip()
            description = request.POST.get("project_description", "").strip()
            
            if not name:
                messages.error(request, "Project name is required")
                return redirect("dash_track")
            
            # ✅ NORMALIZAR NOMBRE DEL PROYECTO
            normalized_name = clean_project_name(name)
            
            # Crear proyecto
            project = Project.objects.create(
                user=request.user,
                name=normalized_name,
                description=description,
                is_active=True
            )
            
            messages.success(request, f"Project '{normalized_name}' created successfully!")
            return redirect("dash_track")
            
        except Exception as e:
            messages.error(request, f"Error creating project: {str(e)}")
    
    return redirect("dash_track")


#############################
#  EXTRAS DASHBOARD SECTIONS
#############################

@login_required
def account_settings_view(request):
    """Vista para configuración de cuenta - VERSIÓN MEJORADA"""
    try:
        profile = FiscalProfile.objects.get(user=request.user)
        return render(request, "budgidesk_app/account_settings.html", {
            'profile': profile
        })
    except FiscalProfile.DoesNotExist:
        return redirect('onboarding')


def intro_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")  
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
    try:
        profile = FiscalProfile.objects.get(user=request.user)
    except FiscalProfile.DoesNotExist:
        return redirect('onboarding')

    sales_invoices = Invoice.objects.filter(
        user=request.user, 
        invoice_type="sale"
    ).select_related('contact').order_by("-date")

    favorite_customers = Contact.objects.filter(
        user=request.user, 
        is_client=True
    ).order_by("name")

    return render(request, "budgidesk_app/dash/invoice/main_invoice.html", {
        "invoice_count": profile.invoice_count,
        "sales_invoices": sales_invoices,  
        "favorite_customers": favorite_customers,  
    })


#############################
#  CREDIT NOTES
#############################

@login_required
def credit_note_create_view(request):
    """Vista para crear notas de crédito"""
    try:
        profile = FiscalProfile.objects.get(user=request.user)
        return render(request, "budgidesk_app/dash/invoice/credite_note.html", {
            "profile": profile
        })
    except FiscalProfile.DoesNotExist:
        return redirect("onboarding")


@login_required
def credit_note_save_view(request):
    """Guarda una nota de crédito - VERSIÓN SIMPLIFICADA"""
    if request.method != "POST":
        return redirect("credit_note_create")
    
    # Por ahora, redirigir al dashboard
    messages.info(request, "Credit note functionality coming soon!")
    return redirect("dashboard")