import requests
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import ast
import json

# Islamic Finance Terminology Constants
ISLAMIC_TERMS = {
    'vehicle_value': 'Al-Silm (Vehicle Value)',
    'down_payment': 'Al-Masrof (Down Payment)',
    'balance_amount': 'Al-Baqi (Balance Amount)',
    'profit_rate': 'Nisbat Al-Ribh (Profit Rate)',
    'profit_amount': 'Al-Ribh (Profit Amount)',
    'total_financing': 'Al-Mablagh Al-Muwazzaf (Total Financing)',
    'monthly_instalment': 'Al-Qist Al-Shahri (Monthly Instalment)',
    'total_payable': 'Al-Mablagh Al-Mustahiq Kulluh (Total Payable)'
}

# Vehicle type mapping with multiple variations
VEHICLE_TYPE_MAPPING = {
    'standard': ['standard', 'normal', 'regular', 'conventional', 'basic', 'ordinary'],
    'hybrid': ['hybrid', 'hev', 'hybrid electric vehicle', 'electric hybrid', 'eco'],
    'land_cruiser': ['land cruiser', 'landcruiser', 'lc', 'toyota land cruiser', 'land cruiser hybrid'],
    'lx600': ['lx600', 'lexus lx600', 'lx 600', 'lexus lx 600'],
    'lx700': ['lx700', 'lexus lx700', 'lx 700', 'lexus lx 700']
}

# Current profit rates as per new rules (Murabaha profit rates)
CURRENT_PROFIT_RATES = {
    'standard': 0.0575,
    'hybrid': 0.039,
    'land_cruiser': 0.069,
    'lx600': 0.069,
    'lx700': 0.069
}

def _safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float with error handling"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove any commas or currency symbols
            cleaned_value = value.replace(',', '').replace('AED', '').replace('$', '').strip()
            return float(cleaned_value)
        return float(value)
    except (ValueError, TypeError):
        return default

@tool(name="calculate_islamic_financing", description="Calculate Shariah-compliant vehicle financing using Murabaha principles with comprehensive vehicle type support and UAE-specific rules")
def calculate_islamic_financing(
    vehicle_value: float = 65700,
    down_payment: float = 10000,
    tenure_months: int = 48,
    vehicle_type: str = "standard",
    customer_type: str = "individual",
    services_contracts: float = 0,
    comprehensive_insurance: float = 0,
    use_new_rules: bool = True,
    is_repeat_customer: bool = False
) -> Dict[str, Any]:
    """
    Calculate Shariah-compliant vehicle financing using Murabaha (cost-plus) principles.
    Supports all vehicle types including standard, hybrid, Land Cruiser, LX600, LX700 with UAE-specific rules.
    
    Parameters:
    vehicle_value (float): Total value of the vehicle (Al-Silm) in AED
    down_payment (float): Initial down payment (Al-Masrof) in AED
    tenure_months (int): Financing tenure in months (Al-Muddat)
    vehicle_type (str): Type of vehicle - standard, hybrid, land_cruiser, lx600, lx700
    customer_type (str): Customer type - individual or qatari (affects maximum tenure)
    services_contracts (float): Optional services contracts/Takaful amount in AED
    comprehensive_insurance (float): Comprehensive insurance amount in AED
    use_new_rules (bool): Whether to use new rules (5.75% standard) or old rules (6.8% standard)
    is_repeat_customer (bool): Whether customer is repeat IHF client for special rates
    
    Returns:
    Dict[str, Any]: Comprehensive Islamic financing calculation with Shariah compliance details
    """
    
    try:
        # Safely convert all numeric inputs to float
        vehicle_value = _safe_float_convert(vehicle_value, 65700.0)
        down_payment = _safe_float_convert(down_payment, 10000.0)
        tenure_months = int(_safe_float_convert(tenure_months, 48))
        services_contracts = _safe_float_convert(services_contracts, 0.0)
        comprehensive_insurance = _safe_float_convert(comprehensive_insurance, 0.0)
        
        # Normalize vehicle type input
        vehicle_type = _normalize_vehicle_type(vehicle_type)
        
        # Validate inputs
        _validate_inputs(vehicle_value, down_payment, tenure_months, customer_type)
        
        # Calculate down payment percentage
        down_payment_percentage = (down_payment / vehicle_value) * 100
        
        # Get appropriate profit rate based on vehicle type and rules
        profit_rate = _get_profit_rate(vehicle_type, down_payment_percentage, is_repeat_customer, use_new_rules)
        
        # Calculate balance amount (Al-Baqi) - ensure float
        balance_amount = float(vehicle_value) - float(down_payment)
        
        # Calculate profit amount (Al-Ribh) using flat rate method for Murabaha
        # Ensure all values are float before calculation
        profit_amount = float(balance_amount) * float(profit_rate) * (float(tenure_months) / 12.0)
        
        # Calculate total financing amount (Al-Mablagh Al-Muwazzaf)
        total_financing_amount = float(balance_amount) + float(profit_amount)
        
        # Calculate monthly instalment (Al-Qist Al-Shahri)
        monthly_instalment = float(total_financing_amount) / float(tenure_months)
        
        # Calculate total payable amount
        total_payable = float(total_financing_amount) + float(down_payment)
        
        # Calculate additional costs
        total_additional_costs = float(services_contracts) + float(comprehensive_insurance)
        grand_total = float(total_payable) + total_additional_costs
        
        # Prepare comprehensive Islamic financing result
        result = {
            'success': True,
            'calculation_timestamp': datetime.now().isoformat(),
            'shariah_compliant': True,
            'financing_model': 'Murabaha (Cost-Plus)',
            
            # Input parameters
            'input_parameters': {
                'vehicle_value': vehicle_value,
                'down_payment': down_payment,
                'tenure_months': tenure_months,
                'vehicle_type': vehicle_type,
                'customer_type': customer_type,
                'services_contracts': services_contracts,
                'comprehensive_insurance': comprehensive_insurance,
                'use_new_rules': use_new_rules,
                'is_repeat_customer': is_repeat_customer
            },
            
            # Financial breakdown
            'financial_breakdown': {
                'vehicle_value_aed': round(float(vehicle_value), 2),
                'down_payment_aed': round(float(down_payment), 2),
                'down_payment_percentage': round(float(down_payment_percentage), 2),
                'balance_amount_aed': round(float(balance_amount), 2),
                'profit_rate_percentage': round(float(profit_rate) * 100, 3),
                'profit_amount_aed': round(float(profit_amount), 2),
                'total_financing_amount_aed': round(float(total_financing_amount), 2),
                'monthly_instalment_aed': round(float(monthly_instalment), 2),
                'total_payable_aed': round(float(total_payable), 2)
            },
            
            # Islamic terminology
            'islamic_terminology': ISLAMIC_TERMS,
            
            # Additional costs summary
            'additional_costs': {
                'services_contracts_aed': round(float(services_contracts), 2),
                'comprehensive_insurance_aed': round(float(comprehensive_insurance), 2),
                'total_additional_costs_aed': round(float(total_additional_costs), 2),
                'grand_total_aed': round(float(grand_total), 2)
            },
            
            # Business rules applied
            'business_rules_applied': {
                'max_tenure_months': 60 if customer_type.lower() == 'qatari' else 48,
                'rules_version': 'new_rules_2024' if use_new_rules else 'old_rules',
                'repeat_customer_discount': 'applied' if is_repeat_customer else 'not_applied',
                'vehicle_specific_rates': 'applied'
            }
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Calculation error: {str(e)}",
            'calculation_timestamp': datetime.now().isoformat(),
            'shariah_compliant': True
        }

def _normalize_vehicle_type(vehicle_input: str) -> str:
    """Normalize vehicle type input to standard values"""
    if not vehicle_input:
        return 'standard'
    
    vehicle_input_lower = str(vehicle_input).lower().strip()
    
    for standard_value, variations in VEHICLE_TYPE_MAPPING.items():
        if vehicle_input_lower in variations or any(variation in vehicle_input_lower for variation in variations):
            return standard_value
    
    # Fallback to partial matching
    if any(keyword in vehicle_input_lower for keyword in ['hybrid', 'hev', 'electric']):
        return 'hybrid'
    elif any(keyword in vehicle_input_lower for keyword in ['land cruiser', 'landcruiser', 'lc']):
        return 'land_cruiser'
    elif any(keyword in vehicle_input_lower for keyword in ['lx600', 'lx 600']):
        return 'lx600'
    elif any(keyword in vehicle_input_lower for keyword in ['lx700', 'lx 700']):
        return 'lx700'
    else:
        return 'standard'

def _validate_inputs(vehicle_value: float, down_payment: float, tenure_months: int, customer_type: str):
    """Validate all input parameters"""
    if vehicle_value <= 0:
        raise ValueError("Vehicle value must be positive")
    
    if down_payment <= 0:
        raise ValueError("Down payment must be positive")
    
    if down_payment >= vehicle_value:
        raise ValueError("Down payment must be less than vehicle value")
    
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")
    
    # Validate tenure based on customer type
    max_tenure = 60 if customer_type.lower() == 'qatari' else 48
    if tenure_months > max_tenure:
        raise ValueError(f"Maximum tenure for {customer_type} customers is {max_tenure} months")

def _get_profit_rate(vehicle_type: str, down_payment_percentage: float, is_repeat_customer: bool, use_new_rules: bool) -> float:
    """Determine appropriate profit rate based on vehicle type and conditions"""
    # Ensure down_payment_percentage is float
    down_payment_percentage = _safe_float_convert(down_payment_percentage, 0.0)
    
    if use_new_rules:
        base_rate = CURRENT_PROFIT_RATES.get(vehicle_type, CURRENT_PROFIT_RATES['standard'])
    else:
        # Old rules logic
        if vehicle_type == 'hybrid':
            base_rate = 0.049  # 4.9% for HEV
        elif vehicle_type in ['land_cruiser', 'lx600', 'lx700'] and down_payment_percentage < 50:
            base_rate = 0.0816  # 8.16% for LC/LX with <50% down payment
        else:
            base_rate = 0.068  # 6.8% standard
    
    # Apply repeat customer discount
    if is_repeat_customer:
        base_rate = float(base_rate) * 0.90  # 10% discount for repeat customers
    
    return float(base_rate)

@tool(name="get_available_vehicle_types", description="Get list of supported vehicle types and their current profit rates")
def get_available_vehicle_types(use_new_rules: bool = True) -> Dict[str, Any]:
    """
    Get comprehensive list of supported vehicle types and their current profit rates
    
    Parameters:
    use_new_rules (bool): Whether to show new rules rates or old rules rates
    
    Returns:
    Dict[str, Any]: Available vehicle types with descriptions and rates
    """
    
    vehicle_types_info = {}
    
    for vehicle_type, variations in VEHICLE_TYPE_MAPPING.items():
        rate = _get_profit_rate(vehicle_type, 20, False, use_new_rules)  # 20% down payment for sample
        vehicle_types_info[vehicle_type] = {
            'description': variations[0].title(),
            'example_variations': variations[:3],
            'profit_rate_percentage': round(float(rate) * 100, 3),
            'rules_applied': 'new_rules_2024' if use_new_rules else 'old_rules'
        }
    
    return {
        'success': True,
        'vehicle_types': vehicle_types_info,
        'rules_version': 'new_rules_2024' if use_new_rules else 'old_rules',
        'timestamp': datetime.now().isoformat()
    }

@tool(name="calculate_multiple_scenarios", description="Calculate multiple financing scenarios for comparison")
def calculate_multiple_scenarios(
    vehicle_value: float = 65700,
    down_payments: List[float] = [10000, 15000, 20000],
    tenures: List[int] = [36, 48, 60],
    vehicle_type: str = "standard",
    customer_type: str = "individual"
) -> Dict[str, Any]:
    """
    Calculate multiple financing scenarios for easy comparison
    
    Parameters:
    vehicle_value (float): Total value of the vehicle in AED
    down_payments (List[float]): List of down payment amounts to compare
    tenures (List[int]): List of tenure periods to compare
    vehicle_type (str): Type of vehicle
    customer_type (str): Customer type
    
    Returns:
    Dict[str, Any]: Multiple scenario calculations for comparison
    """
    
    scenarios = []
    
    for down_payment in down_payments:
        for tenure in tenures:
            try:
                result = calculate_islamic_financing(
                    vehicle_value=vehicle_value,
                    down_payment=down_payment,
                    tenure_months=tenure,
                    vehicle_type=vehicle_type,
                    customer_type=customer_type
                )
                
                if result['success']:
                    financial_data = result['financial_breakdown']
                    scenarios.append({
                        'down_payment_aed': _safe_float_convert(down_payment),
                        'down_payment_percentage': financial_data['down_payment_percentage'],
                        'tenure_months': int(tenure),
                        'monthly_instalment_aed': financial_data['monthly_instalment_aed'],
                        'total_payable_aed': financial_data['total_payable_aed'],
                        'profit_amount_aed': financial_data['profit_amount_aed']
                    })
            except Exception as e:
                # Log the error but continue with other scenarios
                print(f"Warning: Scenario failed for down_payment={down_payment}, tenure={tenure}: {e}")
                continue
    
    # Sort scenarios by monthly instalment
    scenarios.sort(key=lambda x: x['monthly_instalment_aed'])
    
    return {
        'success': True,
        'scenarios_count': len(scenarios),
        'comparison_parameters': {
            'vehicle_value': _safe_float_convert(vehicle_value),
            'vehicle_type': vehicle_type,
            'customer_type': customer_type
        },
        'scenarios': scenarios,
        'timestamp': datetime.now().isoformat()
    }

# Example usage with default values
if __name__ == "__main__":
    # Test the main financing calculation
    result = calculate_islamic_financing()
    
    if result['success']:
        print("🕌 ISLAMIC FINANCING CALCULATION RESULTS")
        print("=" * 60)
        
        financial = result['financial_breakdown']
        print(f"Vehicle Value: AED {financial['vehicle_value_aed']:,.2f}")
        print(f"Down Payment: AED {financial['down_payment_aed']:,.2f} ({financial['down_payment_percentage']:.1f}%)")
        print(f"Balance Amount: AED {financial['balance_amount_aed']:,.2f}")
        print(f"Profit Rate: {financial['profit_rate_percentage']:.3f}%")
        print(f"Profit Amount: AED {financial['profit_amount_aed']:,.2f}")
        print(f"Total Financing: AED {financial['total_financing_amount_aed']:,.2f}")
        print(f"Monthly Instalment: AED {financial['monthly_instalment_aed']:,.2f}")
        print(f"Total Payable: AED {financial['total_payable_aed']:,.2f}")
        
        print(f"\n📊 Business Rules:")
        for rule, value in result['business_rules_applied'].items():
            print(f"  {rule}: {value}")
            
        print(f"\n✅ Shariah Compliant: {result['shariah_compliant']}")
        print(f"📅 Calculation Time: {result['calculation_timestamp']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test vehicle types
    print("\n" + "=" * 60)
    vehicle_types = get_available_vehicle_types()
    if vehicle_types['success']:
        print("🚗 AVAILABLE VEHICLE TYPES:")
        for v_type, info in vehicle_types['vehicle_types'].items():
            print(f"  {v_type}: {info['profit_rate_percentage']}% - {info['description']}")