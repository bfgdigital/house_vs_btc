# calcs.py

import numpy_financial as npf
import pandas as pd
import numpy as np


def adjust_for_inflation(value: float, inflation_rate: float, year: int) -> float:
    """
    Adjusts a nominal value for inflation to reflect its purchasing power.

    Parameters:
    - value: The nominal value to adjust.
    - inflation_rate: Annual inflation rate (decimal).
    - year: The year number (integer).

    Returns:
    - The value adjusted for inflation.
    """
    if inflation_rate < -1:
        raise ValueError("Inflation rate cannot be less than -100%.")
    if year < 1:
        raise ValueError("Year must be at least 1.")
    return value / ((1 + inflation_rate) ** (year - 1))



def calculate_additional_visualizations(house_data, btc_data, inflation_rate, cgt_rate, years_range):
    # Existing calculations
    house_net_gain = house_data['Equity (AUD)'] - house_data['Cumulative Investment (AUD)']
    btc_net_gain = btc_data['After Tax BTC Value (AUD)'] - btc_data['Cumulative Investment (AUD)']

    # Inflation-adjusted calculations
    inflation_adjusted_house_equity = [
        adjust_for_inflation(equity, inflation_rate, year)
        for equity, year in zip(house_data['Equity (AUD)'], years_range)
    ]
    inflation_adjusted_btc_value = [
        adjust_for_inflation(value, inflation_rate, year)
        for value, year in zip(btc_data['After Tax BTC Value (AUD)'], years_range)
    ]

    return {
        'house_net_gain': house_net_gain,
        'btc_net_gain': btc_net_gain,
        'cumulative_house_costs': np.cumsum(house_data['Annual Interest (AUD)'] + house_data['Annual Property Costs (AUD)']),
        'cumulative_rent_costs': btc_data['Cumulative Rent Paid (AUD)'],
        'btc_value_after_cgt': btc_data['After Tax BTC Value (AUD)'],
        'house_equity_pp': inflation_adjusted_house_equity,
        'btc_value_pp': inflation_adjusted_btc_value
    }