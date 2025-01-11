# calcs/housing_calcs.py

from dataclasses import dataclass
from typing import List, Tuple, Dict
import numpy as np
import pandas as pd
import numpy_financial as npf


from .utils import adjust_for_inflation


@dataclass
class HousePurchase:
    house_price: float
    deposit: float
    annual_house_growth_rate: float
    mortgage_interest_rate: float
    mortgage_term_years: int
    years_to_simulate: int
    annual_property_costs: float
    inflation_rate: float


@dataclass
class MortgageAmortizationSchedule:
    month: List[int]
    interest: List[float]
    principal: List[float]
    balance: List[float]
    year: List[int]
    schedule_df: pd.DataFrame


@dataclass
class HouseInvestmentDetails:
    house_values: List[float]
    mortgage_balances: List[float]
    equities: List[float]
    annual_interest: List[float]
    annual_principal: List[float]
    annual_property_costs: List[float]
    cumulative_investment_house: List[float]
    amortization_schedule: MortgageAmortizationSchedule


@dataclass
class MortgageDetails:
    loan_amount: float
    lmi_cost: float
    monthly_mortgage_payment: float
    weekly_mortgage_payment: float
    monthly_income: float
    monthly_surplus: float


@dataclass
class RentDetails:
    initial_annual_rent: float
    annual_rent_paid: List[float]
    cumulative_rent_paid: np.ndarray


def calculate_lmi(loan_amount: float, property_value: float) -> float:
    """
    Calculates Lenders Mortgage Insurance (LMI) based on Loan-to-Value Ratio (LVR).
    
    Parameters:
    - loan_amount: The amount of the loan.
    - property_value: The value of the property.
    
    Returns:
    - The LMI cost.
    """
    if property_value <= 0:
        raise ValueError("Property value must be greater than zero.")
    if loan_amount < 0:
        raise ValueError("Loan amount cannot be negative.")
    
    lvr = loan_amount / property_value
    if lvr <= 0.8:
        return 0.0
    elif lvr <= 0.85:
        return loan_amount * 0.005
    elif lvr <= 0.9:
        return loan_amount * 0.01
    elif lvr <= 0.95:
        return loan_amount * 0.02
    else:
        return loan_amount * 0.03


def generate_mortgage_amortization_schedule(
    loan_amount: float,
    annual_interest_rate: float,
    mortgage_term_years: int,
    extra_payment_per_month: float = 0.0
) -> MortgageAmortizationSchedule:
    """
    Generates a mortgage amortization schedule.
    
    Parameters:
    - loan_amount: The principal loan amount.
    - annual_interest_rate: Annual interest rate (decimal).
    - mortgage_term_years: Term of the mortgage in years.
    - extra_payment_per_month: Additional payment per month.
    
    Returns:
    - MortgageAmortizationSchedule dataclass containing the schedule.
    """
    if loan_amount <= 0:
        raise ValueError("Loan amount must be greater than zero.")
    if annual_interest_rate < 0:
        raise ValueError("Annual interest rate cannot be negative.")
    if mortgage_term_years <= 0:
        raise ValueError("Mortgage term must be positive.")
    if extra_payment_per_month < 0:
        raise ValueError("Extra payment per month cannot be negative.")
    
    monthly_interest_rate = annual_interest_rate / 12
    total_payments = mortgage_term_years * 12
    monthly_payment = -npf.pmt(monthly_interest_rate, total_payments, loan_amount)
    
    balance = loan_amount
    schedule = []
    months = []
    interests = []
    principals = []
    balances = []
    years = []
    
    for n in range(1, total_payments + 1):
        interest = balance * monthly_interest_rate
        principal = monthly_payment + extra_payment_per_month - interest
        if principal > balance:
            principal = balance
            balance = 0
        else:
            balance -= principal
        schedule.append({
            'Month': n,
            'Interest': interest,
            'Principal': principal,
            'Balance': balance,
            'Year': (n - 1) // 12 + 1
        })
        months.append(n)
        interests.append(interest)
        principals.append(principal)
        balances.append(balance)
        years.append((n - 1) // 12 + 1)
        if balance <= 0:
            break
    
    schedule_df = pd.DataFrame(schedule)
    
    return MortgageAmortizationSchedule(
        month=months,
        interest=interests,
        principal=principals,
        balance=balances,
        year=years,
        schedule_df=schedule_df
    )


def simulate_house_investment(
    house_purchase: HousePurchase
) -> HouseInvestmentDetails:
    """
    Simulates house investment details over a specified number of years.
    
    Parameters:
    - house_purchase: HousePurchase dataclass containing purchase parameters.
    
    Returns:
    - HouseInvestmentDetails dataclass containing simulation results.
    """
    # Input Validation
    if house_purchase.house_price <= 0:
        raise ValueError("House price must be greater than zero.")
    if house_purchase.deposit < 0:
        raise ValueError("Deposit cannot be negative.")
    if house_purchase.mortgage_interest_rate < 0:
        raise ValueError("Mortgage interest rate cannot be negative.")
    if house_purchase.annual_house_growth_rate < 0:
        raise ValueError("Annual house growth rate cannot be negative.")
    if house_purchase.annual_property_costs < 0:
        raise ValueError("Annual property costs cannot be negative.")
    if house_purchase.inflation_rate < -1:
        raise ValueError("Inflation rate cannot be less than -100%.")
    
    # Calculate Loan Amount
    loan_amount = house_purchase.house_price - house_purchase.deposit
    if loan_amount < 0:
        raise ValueError("Deposit cannot exceed house price.")
    
    # Generate Amortization Schedule
    amortization_schedule = generate_mortgage_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=house_purchase.mortgage_interest_rate,
        mortgage_term_years=house_purchase.mortgage_term_years,
        extra_payment_per_month=0.0  # Assuming no extra payments
    )
    
    # Calculate Annual Totals
    annual_interest = amortization_schedule.schedule_df.groupby('Year')['Interest'].sum().tolist()
    annual_principal = amortization_schedule.schedule_df.groupby('Year')['Principal'].sum().tolist()
    
    # Initialize Variables
    house_values = []
    mortgage_balances = []
    equities = []
    annual_costs_list = []
    cumulative_investment_house = []
    total_invested_house = house_purchase.deposit
    balance = loan_amount
    
    for year in range(1, house_purchase.years_to_simulate + 1):
        # House value with growth
        house_value = house_purchase.house_price * ((1 + house_purchase.annual_house_growth_rate) ** year)
        house_values.append(house_value)
        
        # Update mortgage balance
        if year <= len(annual_principal):
            principal_paid = annual_principal[year - 1]
            balance -= principal_paid
            balance = max(balance, 0.0)
        mortgage_balances.append(balance)
        
        # Annual costs with inflation
        annual_costs = house_purchase.annual_property_costs * ((1 + house_purchase.inflation_rate) ** (year - 1))
        annual_costs_list.append(annual_costs)
        
        # Calculate equity
        equity = house_value - balance
        equities.append(equity)
        
        # Update cumulative investment
        if year <= len(annual_principal):
            total_invested_house += annual_principal[year - 1] + annual_costs
        else:
            total_invested_house += annual_costs
        cumulative_investment_house.append(total_invested_house)
    
    # Extend annual_interest and annual_principal lists if needed
    while len(annual_interest) < house_purchase.years_to_simulate:
        annual_interest.append(0.0)
    while len(annual_principal) < house_purchase.years_to_simulate:
        annual_principal.append(0.0)
    
    return HouseInvestmentDetails(
        house_values=house_values[:house_purchase.years_to_simulate],
        mortgage_balances=mortgage_balances[:house_purchase.years_to_simulate],
        equities=equities[:house_purchase.years_to_simulate],
        annual_interest=annual_interest[:house_purchase.years_to_simulate],
        annual_principal=annual_principal[:house_purchase.years_to_simulate],
        annual_property_costs=annual_costs_list[:house_purchase.years_to_simulate],
        cumulative_investment_house=cumulative_investment_house[:house_purchase.years_to_simulate],
        amortization_schedule=amortization_schedule
    )


def calculate_mortgage_details(
    house_purchase: HousePurchase,
    annual_income: float,
) -> MortgageDetails:
    """
    Calculates mortgage financial details, including loan amount with LMI, payments, and surplus.
    
    Parameters:
    - house_purchase: HousePurchase dataclass containing purchase parameters.
    - annual_income: Annual income.
    
    Returns:
    - MortgageDetails dataclass containing mortgage financial details.
    """
    if annual_income < 0:
        raise ValueError("Annual income cannot be negative.")
    
    # Calculate Loan Amount
    loan_amount = house_purchase.house_price - house_purchase.deposit
    if loan_amount < 0:
        raise ValueError("Deposit cannot exceed house price.")
    
    # Calculate LMI
    lmi_cost = calculate_lmi(loan_amount=loan_amount, property_value=house_purchase.house_price)
    
    # Total Loan Amount including LMI
    total_loan_amount = loan_amount + lmi_cost
    
    # Calculate Monthly Mortgage Payment
    monthly_interest_rate = house_purchase.mortgage_interest_rate / 12
    total_payments = house_purchase.mortgage_term_years * 12
    monthly_mortgage_payment = -npf.pmt(
        rate=monthly_interest_rate,
        nper=total_payments,
        pv=total_loan_amount
    )
    
    # Calculate Weekly Mortgage Payment
    weekly_mortgage_payment = monthly_mortgage_payment * 12 / 52
    
    # Calculate Monthly Income and Surplus
    monthly_income = annual_income / 12
    monthly_surplus = monthly_income - monthly_mortgage_payment
    
    return MortgageDetails(
        loan_amount=total_loan_amount,
        lmi_cost=lmi_cost,
        monthly_mortgage_payment=monthly_mortgage_payment,
        weekly_mortgage_payment=weekly_mortgage_payment,
        monthly_income=monthly_income,
        monthly_surplus=monthly_surplus
    )


def calculate_annual_rent_paid(
    annual_interest: List[float],
    inflation_rate: float,
    years_to_simulate: int
) -> RentDetails:
    """
    Calculates annual rent paid over the simulation period, adjusted for inflation.
    
    Parameters:
    - annual_interest: List of annual interest payments.
    - inflation_rate: Annual inflation rate (decimal).
    - years_to_simulate: Number of years to simulate.
    
    Returns:
    - RentDetails dataclass containing rent payment details.
    """
    if not annual_interest:
        raise ValueError("annual_interest list cannot be empty.")
    if inflation_rate < -1:
        raise ValueError("Inflation rate cannot be less than -100%.")
    if years_to_simulate <= 0:
        raise ValueError("years_to_simulate must be positive.")
    
    initial_annual_rent = annual_interest[0]
    annual_rent_paid = [
        initial_annual_rent * ((1 + inflation_rate) ** (year - 1))
        for year in range(1, years_to_simulate + 1)
    ]
    cumulative_rent = np.cumsum(annual_rent_paid)
    
    return RentDetails(
        initial_annual_rent=initial_annual_rent,
        annual_rent_paid=annual_rent_paid,
        cumulative_rent_paid=cumulative_rent
    )


def adjust_house_purchasing_power(
    house_values: List[float],
    mortgage_balances: List[float],
    inflation_rate: float,
    years_range: List[int]
) -> Tuple[List[float], List[float]]:
    """
    Adjusts house values and mortgage balances for inflation to determine purchasing power.
    
    Parameters:
    - house_values: List of house values at the end of each year.
    - mortgage_balances: List of mortgage balances at the end of each year.
    - inflation_rate: Annual inflation rate (decimal).
    - years_range: List of simulation years.
    
    Returns:
    - Tuple containing:
        - List of house values adjusted for purchasing power.
        - List of mortgage balances adjusted for purchasing power.
    """
    adjusted_house_values = [
        adjust_for_inflation(value, inflation_rate, year)
        for value, year in zip(house_values, years_range)
    ]
    adjusted_mortgage_balances = [
        adjust_for_inflation(balance, inflation_rate, year)
        for balance, year in zip(mortgage_balances, years_range)
    ]
    return adjusted_house_values, adjusted_mortgage_balances


def simulate_house_purchase_and_investment(
    house_price: float,
    deposit: float,
    annual_house_growth_rate: float,
    mortgage_interest_rate: float,
    mortgage_term_years: int,
    years_to_simulate: int,
    annual_property_costs: float,
    inflation_rate: float,
    annual_income: float,
) -> Dict[str, any]:
    """
    Simulates house purchase and investment over a specified number of years, adjusting for inflation.
    
    Parameters:
    - house_price: The price of the house.
    - deposit: Initial deposit paid for the house.
    - annual_house_growth_rate: Annual growth rate of the house value (decimal).
    - mortgage_interest_rate: Annual mortgage interest rate (decimal).
    - mortgage_term_years: Term of the mortgage in years.
    - years_to_simulate: Number of years to simulate.
    - annual_property_costs: Annual costs associated with owning the property.
    - inflation_rate: Annual inflation rate (decimal).
    - annual_income: Annual income.
    
    Returns:
    - Dictionary containing:
        - 'house_investment_details': HouseInvestmentDetails dataclass.
        - 'mortgage_details': MortgageDetails dataclass.
        - 'rent_details': RentDetails dataclass.
        - 'purchasing_power': Tuple of lists with adjusted house values and mortgage balances.
    """
    # Create HousePurchase Instance
    house_purchase = HousePurchase(
        house_price=house_price,
        deposit=deposit,
        annual_house_growth_rate=annual_house_growth_rate,
        mortgage_interest_rate=mortgage_interest_rate,
        mortgage_term_years=mortgage_term_years,
        years_to_simulate=years_to_simulate,
        annual_property_costs=annual_property_costs,
        inflation_rate=inflation_rate
    )
    
    # Simulate House Investment
    house_investment = simulate_house_investment(house_purchase)
    
    # Calculate Mortgage Details
    mortgage_details = calculate_mortgage_details(
        house_purchase=house_purchase,
        annual_income=annual_income,
    )
    
    # Calculate Annual Rent Paid
    rent_details = calculate_annual_rent_paid(
        annual_interest=house_investment.annual_interest,
        inflation_rate=inflation_rate,
        years_to_simulate=years_to_simulate
    )
    
    # Generate Years Range
    years_range = list(range(1, years_to_simulate + 1))
    
    # Adjust Purchasing Power
    adjusted_house_values, adjusted_mortgage_balances = adjust_house_purchasing_power(
        house_values=house_investment.house_values,
        mortgage_balances=house_investment.mortgage_balances,
        inflation_rate=inflation_rate,
        years_range=years_range
    )
    
    return {
        'house_investment_details': house_investment,
        'mortgage_details': mortgage_details,
        'rent_details': rent_details,
        'purchasing_power': (adjusted_house_values, adjusted_mortgage_balances)
    }
