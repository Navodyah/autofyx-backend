#!/usr/bin/env python
"""
Test script to verify down payment calculation logic.
Tests both ratio-based and absolute amount-based down payments.
"""

def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate monthly EMI given principal, annual interest rate, and loan tenure."""
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def test_scenario(
    name: str,
    salary: float,
    vehicle_price: float,
    down_payment_amount: float | None = None,
    down_payment_ratio: float = 0.5,
    rate: float = 13.0,
    months: int = 60,
):
    """Test a single scenario"""
    print(f"\n{'='*70}")
    print(f"Scenario: {name}")
    print(f"{'='*70}")
    
    # Calculate max EMI (40% of salary)
    max_emi = salary * 0.4
    print(f"Monthly Salary:         {salary:,.0f} LKR")
    print(f"Max EMI (40% of salary): {max_emi:,.0f} LKR")
    print(f"Vehicle Price:          {vehicle_price:,.0f} LKR")
    print(f"Interest Rate:          {rate}% per annum")
    print(f"Loan Tenure:            {months} months")
    
    # Determine down payment
    if down_payment_amount is not None:
        dp = down_payment_amount
        print(f"\nDown Payment Method:    USER SPECIFIED AMOUNT")
        print(f"Down Payment:           {dp:,.0f} LKR")
    else:
        dp = vehicle_price * down_payment_ratio
        print(f"\nDown Payment Method:    RATIO-BASED ({down_payment_ratio*100}%)")
        print(f"Down Payment:           {dp:,.0f} LKR")
    
    # Calculate loan
    loan = vehicle_price - dp
    print(f"Loan Principal:         {loan:,.0f} LKR")
    
    # Calculate EMI
    emi = calculate_emi(loan, rate, months)
    print(f"Monthly EMI:            {emi:,.2f} LKR")
    
    # Check affordability
    emi_percent = (emi / salary) * 100
    is_affordable = emi <= max_emi
    status = "✅ AFFORDABLE" if is_affordable else "❌ NOT AFFORDABLE"
    print(f"EMI as % of Salary:     {emi_percent:.2f}%")
    print(f"Affordability Status:   {status}")
    
    return is_affordable


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DOWN PAYMENT LOGIC TEST SUITE")
    print("="*70)
    
    # Test 1: Default ratio-based down payment
    test_scenario(
        name="Scenario 1: Default 50% down payment ratio",
        salary=250000,
        vehicle_price=3000000,
        down_payment_amount=None,
        down_payment_ratio=0.5,
    )
    
    # Test 2: User-specified down payment (less than default ratio)
    test_scenario(
        name="Scenario 2: User-specified down payment of 500,000 LKR (less than 50%)",
        salary=250000,
        vehicle_price=3000000,
        down_payment_amount=500000,  # User provides exact amount
        down_payment_ratio=0.5,  # Ignored because down_payment_amount is provided
    )
    
    # Test 3: User-specified down payment (more than default ratio)
    test_scenario(
        name="Scenario 3: User-specified down payment of 2,000,000 LKR (more than 50%)",
        salary=250000,
        vehicle_price=3000000,
        down_payment_amount=2000000,  # User pays more upfront
        down_payment_ratio=0.5,
    )
    
    # Test 4: Low down payment - check affordability
    test_scenario(
        name="Scenario 4: Low down payment - vehicle affordability test",
        salary=250000,
        vehicle_price=8000000,
        down_payment_amount=1000000,  # Only 12.5% down
        down_payment_ratio=0.5,
    )
    
    # Test 5: High down payment - should be affordable
    test_scenario(
        name="Scenario 5: High down payment - vehicle affordability test",
        salary=250000,
        vehicle_price=8000000,
        down_payment_amount=5000000,  # 62.5% down
        down_payment_ratio=0.5,
    )
    
    # Test 6: Custom ratio (30%)
    test_scenario(
        name="Scenario 6: Custom 30% down payment ratio (no absolute amount)",
        salary=300000,
        vehicle_price=4000000,
        down_payment_amount=None,  # Use ratio
        down_payment_ratio=0.3,  # 30% down
    )
    
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70 + "\n")

