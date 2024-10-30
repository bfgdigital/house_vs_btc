import numpy_financial as npf
import pandas as pd

# Function to calculate Lenders Mortgage Insurance (LMI)
def calculate_lmi(loan_amount, property_value) -> float:
    """
    Very simple LMI calculator.
    """
    lvr: float = loan_amount / property_value
    if lvr <= 0.8:
        return 0
    elif lvr <= 0.85:
        return loan_amount * 0.005
    elif lvr <= 0.9:
        return loan_amount * 0.01
    elif lvr <= 0.95:
        return loan_amount * 0.02
    else:
        return loan_amount * 0.03

# Function to calculate mortgage amortization details
def mortgage_amortization_schedule(loan_amount, annual_interest_rate, mortgage_term_years, extra_payment_per_month) -> pd.DataFrame:
    monthly_interest_rate: float = annual_interest_rate / 12
    total_payments: int = mortgage_term_years * 12
    monthly_payment = -npf.pmt(monthly_interest_rate, total_payments, loan_amount)
    
    # Initialize variables
    balance: float = loan_amount
    schedule: list = []
    
    for n in range(1, total_payments + 1):
        interest: float = balance * monthly_interest_rate
        principal: float = monthly_payment + extra_payment_per_month - interest
        if principal > balance:
            principal = balance
            balance = 0
        else:
            balance -= principal
        schedule.append({
            'Month': n,
            'Interest': interest,
            'Principal': principal,
            'Balance': balance
        })
        if balance <= 0:
            break
    df = pd.DataFrame(schedule)
    df['Year'] = ((df['Month'] - 1) // 12) + 1
    return df

# Function to calculate home investment details
def home_investment_details(house_price, deposit, annual_house_growth_rate, mortgage_interest_rate, mortgage_term_years, years_to_simulate, annual_property_costs, inflation_rate):
    loan_amount: float = house_price - deposit
    extra_payment_per_month = 0  # Assuming no extra payments
    amortization_schedule: pd.DataFrame = mortgage_amortization_schedule(loan_amount, mortgage_interest_rate, mortgage_term_years, extra_payment_per_month)
    
    # Calculate annual totals
    amortization_schedule['Year'] = ((amortization_schedule['Month'] - 1) // 12) + 1
    annual_interest: list = amortization_schedule.groupby('Year')['Interest'].sum().tolist()
    annual_principal: list = amortization_schedule.groupby('Year')['Principal'].sum().tolist()
    years: int = amortization_schedule['Year'].max()
    
    # Adjust for simulation period
    annual_interest += [0] * (years_to_simulate - years)
    annual_principal += [0] * (years_to_simulate - years)
    
    # Initialize variables
    house_values: list = []
    mortgage_balances: list = []
    equities: list = []
    annual_costs_list: list = []
    balance: float = loan_amount
    cumulative_investment_home: list = []
    total_invested_home: float = deposit  # Start with the deposit
    
    for year in range(1, years_to_simulate + 1):
        # Update house value
        house_value: float = house_price * ((1 + annual_house_growth_rate) ** year)
        house_values.append(house_value)
        
        # Update mortgage balance
        if balance > 0:
            principal_paid = annual_principal[year - 1]
            balance -= principal_paid
            if balance < 0:
                balance = 0
        mortgage_balances.append(balance)
        
        # Annual costs adjusted for inflation
        annual_costs: float = annual_property_costs * ((1 + inflation_rate) ** (year - 1))
        annual_costs_list.append(annual_costs)
        
        # Equity calculation
        equity: float = house_value - balance
        equities.append(equity)
        
        # Cumulative investment (deposit + principal payments + costs)
        total_invested_home += annual_principal[year - 1] + annual_costs
        cumulative_investment_home.append(total_invested_home)
        
    return (house_values[:years_to_simulate], 
            mortgage_balances[:years_to_simulate], 
            equities[:years_to_simulate], 
            annual_interest[:years_to_simulate], 
            annual_principal[:years_to_simulate], 
            annual_costs_list[:years_to_simulate],
            cumulative_investment_home[:years_to_simulate],
            amortization_schedule)

# Function to calculate BTC investment over years with decreasing growth rate
def btc_investment_over_years(initial_investment, initial_btc_price, btc_investment_per_year, btc_growth_rates, years):
    total_btc_holdings: float = initial_investment / initial_btc_price
    total_invested: float = initial_investment
    btc_values: list = []
    total_invested_list: list = []
    btc_holdings_list: list = []
    cumulative_investment_btc: list = []
    
    btc_price_t: float = initial_btc_price
    btc_prices: float  = [btc_price_t]
    
    for year in range(1, years + 1):
        growth_rate: float = btc_growth_rates[year - 1]
        btc_price_t *= (1 + growth_rate)
        btc_prices.append(btc_price_t)
        btc_purchased_t: float = btc_investment_per_year[year - 1] / btc_price_t
        total_btc_holdings += btc_purchased_t
        total_invested += btc_investment_per_year[year - 1]
        btc_value: float = total_btc_holdings * btc_price_t
        btc_values.append(btc_value)
        total_invested_list.append(total_invested)
        btc_holdings_list.append(total_btc_holdings)
        cumulative_investment_btc.append(total_invested)
    return btc_values, total_invested_list, btc_holdings_list, cumulative_investment_btc, btc_prices[1:]

# Function to adjust BTC investment for inflation and CGT
def adjust_btc_for_inflation_and_cgt(btc_values, inflation_rate, cgt_rate, years_range, total_invested_list) -> list:
    adjusted_values: list = []
    for btc_value, year, total_invested in zip(btc_values, years_range, total_invested_list):
        taxable_gain: float = max(0, btc_value - total_invested)
        cgt: float = taxable_gain * cgt_rate
        after_tax_value: float = btc_value - cgt
        inflation_adjusted_value: float = after_tax_value / ((1 + inflation_rate) ** (year - 1))
        adjusted_values.append(inflation_adjusted_value)
    return adjusted_values
