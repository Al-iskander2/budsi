from logic.data_manager import load_data

def calculate_taxes(invoices, purchases):
    """
    ✅ CORREGIDO: Usa los valores REALES de VAT de la base de datos
    invoices: lista de dicts con 'total' y 'vat'
    purchases: lista de dicts con 'total', 'vat_amount', 'net_amount'
    """
    TAX_CREDITS = 4000
    INCOME_TAX_BRACKETS = [(44000, 0.2), (float('inf'), 0.4)]
    USC_BANDS = [
        (0, 12012, 0.005),
        (12012, 25760, 0.02),
        (25760, 70044, 0.045),
        (70044, float('inf'), 0.08)
    ]

    # ✅ USA LOS VALORES REALES DE LA BD - NO RECALCULES
    # VAT recaudado (de ventas) - usa el 'vat' que ya viene calculado
    vat_collected = sum(float(inv.get('vat', 0)) for inv in invoices)
    
    # VAT pagado (de gastos) - usa el 'vat_amount' que ya viene calculado  
    vat_paid = sum(float(pur.get('vat_amount', 0)) for pur in purchases)
    
    # Ingresos brutos (total de ventas)
    gross_income = sum(float(inv.get('total', 0)) for inv in invoices)
    
    # Gastos (net_amount de compras - ya viene como subtotal)
    expenses = sum(float(pur.get('net_amount', 0)) for pur in purchases)

    vat_liability = round(vat_collected - vat_paid, 2)
    taxable_income = round(gross_income - expenses, 2)

    # Income tax (mismo cálculo)
    income_tax = 0
    remaining_income = taxable_income
    for bracket, rate in INCOME_TAX_BRACKETS:
        if remaining_income <= 0:
            break
        amount = min(remaining_income, bracket)
        income_tax += round(amount * rate, 2)
        remaining_income -= amount
    
    net_income_tax = max(0, round(income_tax - TAX_CREDITS, 2))

    # USC (mismo cálculo)
    usc = 0
    remaining_income = round(taxable_income, 2)
    usc_breakdown = []
    for lower, upper, rate in USC_BANDS:
        if remaining_income <= 0:
            break
        band_amount = round(min(remaining_income, upper - lower), 2)
        band_tax = round(band_amount * rate, 2)
        usc += band_tax
        usc_breakdown.append({
            'band': f"€{lower:,.2f} - €{upper:,.2f}",
            'rate': f"{rate*100}%",
            'amount': band_amount,
            'tax': band_tax
        })
        remaining_income -= band_amount
    usc = round(usc, 2)

    prsi = round(max(0, taxable_income) * 0.04, 2)
    total_tax = round(net_income_tax + usc + prsi, 2)

    return {
        'vat': {
            'collected': vat_collected,
            'paid': vat_paid,
            'liability': vat_liability
        },
        'income': {
            'gross': gross_income,
            'expenses': expenses,
            'taxable': taxable_income
        },
        'income_tax': {
            'gross': income_tax,
            'credits': TAX_CREDITS,
            'net': net_income_tax
        },
        'usc': {
            'total': usc,
            'breakdown': usc_breakdown
        },
        'prsi': prsi,
        'total_tax': total_tax,
        'metadata': {
            'currency': 'EUR',
            'calculation_method': 'actual_values_from_db'
        }
    }