# calcs/btc_calcs.py

from dataclasses import dataclass
from typing import List, Tuple, Dict
import numpy as np
import pandas as pd

from .utils import adjust_for_inflation


@dataclass
class BTCInvestment:
    initial_investment: float
    initial_btc_price: float
    annual_investment_amounts: List[float]
    annual_growth_rates: List[float]
    years: int


@dataclass
class BTCSimulationResult:
    years: int
    btc_values: List[float]
    total_invested: List[float]
    btc_holdings: List[float]
    cumulative_invested: List[float]
    btc_prices: List[float]
    annual_invested: List[float]
    initial_btc_price: float

def generate_btc_growth_rates(
    initial_growth_rate: float, 
    final_growth_rate: float, 
    years: int
) -> List[float]:
    """
    Generates a list of BTC growth rates linearly spaced between initial and final rates.

    Parameters:
    - initial_growth_rate: Initial annual growth rate (decimal).
    - final_growth_rate: Final annual growth rate (decimal).
    - years: Number of years to simulate.

    Returns:
    - List of annual growth rates.
    """
    if years <= 0:
        raise ValueError("Number of years must be positive.")
    return list(np.linspace(initial_growth_rate, final_growth_rate, years))


def simulate_btc_investments(
    investment: BTCInvestment
) -> BTCSimulationResult:
    """
    Simulates BTC investments over a specified number of years.

    Parameters:
    - investment: BTCInvestment dataclass containing investment parameters.

    Returns:
    - BTCSimulationResult dataclass containing simulation results.
    """
    # Input Validation
    if len(investment.annual_investment_amounts) != investment.years:
        raise ValueError("Length of annual_investment_amounts must equal years.")
    if len(investment.annual_growth_rates) != investment.years:
        raise ValueError("Length of annual_growth_rates must equal years.")
    if investment.initial_btc_price <= 0:
        raise ValueError("Initial BTC price must be positive.")
    if investment.initial_investment < 0:
        raise ValueError("Initial investment cannot be negative.")
    if any(rate < -1 for rate in investment.annual_growth_rates):
        raise ValueError("Growth rates must be greater than -100%.")
    if any(amount < 0 for amount in investment.annual_investment_amounts):
        raise ValueError("Annual investment amounts cannot be negative.")

    # Initialize Variables
    btc_holdings = investment.initial_investment / investment.initial_btc_price
    total_invested = investment.initial_investment

    btc_values = [btc_holdings * investment.initial_btc_price]
    total_invested_list = [total_invested]
    btc_holdings_list = [btc_holdings]
    cumulative_invested = [total_invested]
    btc_prices = [investment.initial_btc_price]
    annual_invested = [investment.initial_investment]

    # Track each year's investment separately for accurate CGT calculation
    investments_record = [{'investment': investment.initial_investment, 'year_invested': 0}]  # year_invested starts at 0

    for year in range(1, investment.years + 1):
        growth_rate = investment.annual_growth_rates[year - 1]
        new_btc_price = btc_prices[-1] * (1 + growth_rate)
        btc_prices.append(new_btc_price)

        annual_investment = investment.annual_investment_amounts[year - 1]
        btc_purchased = annual_investment / new_btc_price if new_btc_price > 0 else 0
        btc_holdings += btc_purchased
        total_invested += annual_investment

        btc_values.append(btc_holdings * new_btc_price)
        total_invested_list.append(total_invested)
        btc_holdings_list.append(btc_holdings)
        cumulative_invested.append(total_invested)
        annual_invested.append(annual_investment)

        # Record the new investment with the year it was made
        investments_record.append({'investment': annual_investment, 'year_invested': year})

    # Remove initial values to align with simulation years
    btc_values = btc_values[1:]
    total_invested_list = total_invested_list[1:]
    btc_holdings_list = btc_holdings_list[1:]
    cumulative_invested = cumulative_invested[1:]
    btc_prices = btc_prices[1:]
    annual_invested = annual_invested[1:]

    return BTCSimulationResult(
        years=investment.years,
        btc_values=btc_values,
        total_invested=total_invested_list,
        btc_holdings=btc_holdings_list,
        cumulative_invested=cumulative_invested,
        btc_prices=btc_prices,
        annual_invested=annual_invested,
        initial_btc_price=investment.initial_btc_price
    )


def calculate_annual_btc_investment(
    annual_principal_payments: List[float], 
    annual_additional_costs: List[float]
) -> List[float]:
    """
    Calculates the total BTC investment per year by combining principal payments and additional costs.

    Parameters:
    - annual_principal_payments: List of principal payments per year.
    - annual_additional_costs: List of additional costs per year.

    Returns:
    - List of total BTC investment per year.
    """
    if len(annual_principal_payments) != len(annual_additional_costs):
        raise ValueError("annual_principal_payments and annual_additional_costs must have the same length.")

    return [principal + cost for principal, cost in zip(annual_principal_payments, annual_additional_costs)]


def adjust_btc_for_tax(
    simulation_result: BTCSimulationResult,
    investments_record: List[Dict[str, any]],
    cgt_rate: float
) -> List[float]:
    """
    Adjusts BTC values for Capital Gains Tax (CGT), applying discounts based on holding periods.

    Parameters:
    - simulation_result: BTCSimulationResult dataclass containing simulation data.
    - investments_record: List of dictionaries tracking each investment and its year invested.
    - cgt_rate: Capital Gains Tax rate (decimal).

    Returns:
    - List of BTC values after tax adjustments.
    """
    after_tax_values = []
    cumulative_btc_value = 0.0

    for year in range(1, simulation_result.years + 1):
        # Current BTC price
        btc_price = simulation_result.btc_prices[year - 1]
        # Current total BTC holdings
        btc_holdings = simulation_result.btc_holdings[year - 1]
        # Current BTC value
        current_value = btc_holdings * btc_price

        # Calculate total invested up to this year
        total_invested = simulation_result.total_invested[year - 1]

        # Calculate gains for each investment
        total_tax = 0.0
        for investment in investments_record:
            investment_amount = investment['investment']
            year_invested = investment['year_invested']
            holding_period = year - year_invested
            if holding_period <= 0:
                continue  # Investment made this year, no gain yet
            # Calculate current value of this investment
            btc_purchased = investment_amount / simulation_result.btc_prices[year_invested - 1] if investment['year_invested'] > 0 else investment_amount / simulation_result.initial_btc_price
            current_investment_value = btc_purchased * btc_price
            gain = current_investment_value - investment_amount
            if gain > 0:
                # Apply 50% CGT discount if held for more than 1 year
                discount = 0.5 if holding_period > 1 else 1.0
                cgt = gain * cgt_rate * discount
                total_tax += cgt

        # Adjust current value after tax
        after_tax_value = current_value - total_tax
        after_tax_values.append(after_tax_value)

    return after_tax_values


def adjust_btc_purchasing_power(
    after_tax_values: List[float], 
    inflation_rate: float, 
    years_range: List[int]
) -> List[float]:
    """
    Adjusts BTC values for inflation to determine purchasing power.

    Parameters:
    - after_tax_values: List of BTC values after tax adjustments.
    - inflation_rate: Annual inflation rate (decimal).
    - years_range: List of simulation years.

    Returns:
    - List of BTC values adjusted for purchasing power.
    """
    purchasing_power_values = [
        adjust_for_inflation(value, inflation_rate, year)
        for value, year in zip(after_tax_values, years_range)
    ]
    return purchasing_power_values


def adjust_btc_for_tax_and_purchasing_power(
    simulation_result: BTCSimulationResult,
    investments_record: List[Dict[str, any]],
    cgt_rate: float,
    inflation_rate: float
) -> Tuple[List[float], List[float]]:
    """
    Adjusts BTC values for Capital Gains Tax (CGT) and purchasing power.

    Parameters:
    - simulation_result: BTCSimulationResult dataclass containing simulation data.
    - investments_record: List of dictionaries tracking each investment and its year invested.
    - cgt_rate: Capital Gains Tax rate (decimal).
    - inflation_rate: Annual inflation rate (decimal).

    Returns:
    - Tuple containing:
        - List of BTC values after tax adjustments.
        - List of BTC values adjusted for purchasing power.
    """
    after_tax_values = adjust_btc_for_tax(
        simulation_result=simulation_result,
        investments_record=investments_record,
        cgt_rate=cgt_rate
    )

    years_range = list(range(1, simulation_result.years + 1))
    purchasing_power = adjust_btc_purchasing_power(
        after_tax_values=after_tax_values,
        inflation_rate=inflation_rate,
        years_range=years_range
    )

    return after_tax_values, purchasing_power


def simulate_and_adjust_btc_investment(
    initial_investment: float,
    initial_btc_price: float,
    annual_investment_amounts: List[float],
    initial_growth_rate: float,
    final_growth_rate: float,
    years: int,
    cgt_rate: float,
    inflation_rate: float
) -> Dict[str, any]:
    """
    Simulates BTC investments over the specified years and adjusts for taxes and inflation.

    Parameters:
    - initial_investment: Initial amount invested in BTC.
    - initial_btc_price: Price of BTC at the start.
    - annual_investment_amounts: List of additional investments per year.
    - initial_growth_rate: Starting annual growth rate for BTC.
    - final_growth_rate: Ending annual growth rate for BTC.
    - years: Number of years to simulate.
    - cgt_rate: Capital Gains Tax rate (decimal).
    - inflation_rate: Annual inflation rate (decimal).

    Returns:
    - Dictionary containing:
        - 'simulation_result': BTCSimulationResult dataclass.
        - 'after_tax_values': List of BTC values after tax.
        - 'purchasing_power': List of BTC values adjusted for purchasing power.
    """
    # Generate Growth Rates
    annual_growth_rates = generate_btc_growth_rates(
        initial_growth_rate=initial_growth_rate,
        final_growth_rate=final_growth_rate,
        years=years
    )

    # Create Investment Instance
    investment = BTCInvestment(
        initial_investment=initial_investment,
        initial_btc_price=initial_btc_price,
        annual_investment_amounts=annual_investment_amounts,
        annual_growth_rates=annual_growth_rates,
        years=years
    )

    # Simulate Investments
    simulation_result = simulate_btc_investments(investment)

    # Track each investment's details for accurate CGT calculation
    investments_record = [{'investment': investment.initial_investment, 'year_invested': 0}]
    for year in range(1, years + 1):
        annual_investment = investment.annual_investment_amounts[year - 1]
        investments_record.append({'investment': annual_investment, 'year_invested': year})

    # Adjust for Tax and Purchasing Power
    after_tax_values, purchasing_power = adjust_btc_for_tax_and_purchasing_power(
        simulation_result=simulation_result,
        investments_record=investments_record,
        cgt_rate=cgt_rate,
        inflation_rate=inflation_rate
    )

    return {
        'simulation_result': simulation_result,
        'after_tax_values': after_tax_values,
        'purchasing_power': purchasing_power
    }
