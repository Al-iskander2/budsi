from decimal import Decimal

def calculate_taxes(sales_invoices, purchase_invoices):
    """
    ✅ CORREGIDO: Trabaja con objetos Invoice reales
    """
    TAX_CREDITS = Decimal('4000')
    INCOME_TAX_BRACKETS = [(Decimal('44000'), Decimal('0.20')), (Decimal('9999999'), Decimal('0.40'))]
    USC_BANDS = [
        (Decimal('0'), Decimal('12012'), Decimal('0.005')),
        (Decimal('12012'), Decimal('25760'), Decimal('0.02')),
        (Decimal('25760'), Decimal('70044'), Decimal('0.045')),
        (Decimal('70044'), Decimal('9999999'), Decimal('0.08'))
    ]

    # ✅ USAR ATRIBUTOS DE OBJETOS INVOICE
    vat_collected = sum(inv.vat_amount for inv in sales_invoices) if sales_invoices else Decimal('0')
    vat_paid = sum(inv.vat_amount for inv in purchase_invoices) if purchase_invoices else Decimal('0')
    
    gross_income = sum(inv.total for inv in sales_invoices) if sales_invoices else Decimal('0')
    expenses = sum(inv.total for inv in purchase_invoices) if purchase_invoices else Decimal('0')

    vat_liability = vat_collected - vat_paid
    taxable_income = gross_income - expenses

    # Income tax calculation
    income_tax = Decimal('0')
    remaining_income = taxable_income
    for bracket, rate in INCOME_TAX_BRACKETS:
        if remaining_income <= Decimal('0'):
            break
        amount = min(remaining_income, bracket)
        income_tax += amount * rate
        remaining_income -= amount
    
    net_income_tax = max(Decimal('0'), income_tax - TAX_CREDITS)

    # USC calculation
    usc = Decimal('0')
    remaining_income = taxable_income
    usc_breakdown = []
    for lower, upper, rate in USC_BANDS:
        if remaining_income <= Decimal('0'):
            break
        band_amount = min(remaining_income, upper - lower)
        band_tax = band_amount * rate
        usc += band_tax
        usc_breakdown.append({
            'band': f"€{lower:,.2f} - €{upper:,.2f}",
            'rate': f"{rate*100}%",
            'amount': float(band_amount),
            'tax': float(band_tax)
        })
        remaining_income -= band_amount

    prsi = max(Decimal('0'), taxable_income) * Decimal('0.04')
    total_tax = net_income_tax + usc + prsi

    return {
        'vat': {
            'collected': float(vat_collected),
            'paid': float(vat_paid),
            'liability': float(vat_liability)
        },
        'income': {
            'gross': float(gross_income),
            'expenses': float(expenses),
            'taxable': float(taxable_income)
        },
        'income_tax': {
            'gross': float(income_tax),
            'credits': float(TAX_CREDITS),
            'net': float(net_income_tax)
        },
        'usc': {
            'total': float(usc),
            'breakdown': usc_breakdown
        },
        'prsi': float(prsi),
        'total_tax': float(total_tax)
    }