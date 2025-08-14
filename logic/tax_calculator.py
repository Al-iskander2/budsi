from logic.data_manager import load_data

def calculate_taxes():
    # Constantes fiscales (actualizadas para coincidir con Excel)
    VAT_RATE = 0.23
    TAX_CREDITS = 4000
    INCOME_TAX_BRACKETS = [(44000, 0.2), (float('inf'), 0.4)]
    USC_BANDS = [
        (0, 12012, 0.005),
        (12012, 25760, 0.02),
        (25760, 70044, 0.045),
        (70044, float('inf'), 0.08)
    ]

    # Cargar datos
    invoices = load_data('invoices.csv')
    purchases = load_data('purchases.csv')

    # -- Cálculos compatibles con Excel --
    # 1. Para facturas de VENTA (usar total como bruto)
    vat_collected = sum(float(inv['total']) * VAT_RATE / (1 + VAT_RATE) for inv in invoices)
    gross_income_net = sum(float(inv['total']) / (1 + VAT_RATE) for inv in invoices)  # Neto
    
    # 2. Para facturas de COMPRA (usar total como bruto)
    vat_paid = sum(float(pur['total']) * VAT_RATE / (1 + VAT_RATE) for pur in purchases)
    expenses_net = sum(float(pur['total']) / (1 + VAT_RATE) for pur in purchases)  # Neto
    
    # 3. Ajustar redondeos como en Excel
    vat_collected = round(vat_collected, 2)
    vat_paid = round(vat_paid, 2)
    gross_income_net = round(gross_income_net, 2)
    expenses_net = round(expenses_net, 2)
    
    vat_liability = round(vat_collected - vat_paid, 2)
    taxable_income = round(gross_income_net - expenses_net, 2)

    # -- Income Tax (ajustado) --
    income_tax = 0
    remaining_income = taxable_income
    
    for bracket, rate in INCOME_TAX_BRACKETS:
        if remaining_income <= 0:
            break
        amount = min(remaining_income, bracket)
        income_tax += round(amount * rate, 2)  # Redondeo explícito
        remaining_income -= amount
    
    net_income_tax = max(0, round(income_tax - TAX_CREDITS, 2))

    # -- USC (con redondeos) --
    usc = 0
    remaining_income = round(taxable_income, 2)  # Base para USC = Ingresos netos
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

    # -- PRSI --
    prsi = round(max(0, taxable_income) * 0.04, 2)
    total_tax = round(net_income_tax + usc + prsi, 2)

    return {
        'vat': {
            'collected': vat_collected,
            'paid': vat_paid,
            'liability': vat_liability
        },
        'income': {
            'gross': gross_income_net,  # NETO (sin IVA)
            'expenses': expenses_net,   
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
            'vat_rate': VAT_RATE,
            'currency': 'EUR',
            'calculation_method': 'net_base'
        }
    }