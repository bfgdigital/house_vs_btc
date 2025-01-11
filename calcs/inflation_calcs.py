# /calcs/inflation_calcs.py

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Tuple

def load_and_process_cpi(
    file_path: str = 'data/640101.xlsx',
    sheet_name: str = 'Data1',
    selected_periods: List[int] = None
) -> Tuple[pd.DataFrame, List[str], datetime, pd.DataFrame]:
    """
    Load and process CPI data from an Excel file with multi-row headers.

    Parameters:
    - file_path (str): Path to the Excel file.
    - sheet_name (str): Sheet name to read data from.
    - selected_periods (List[int], optional): List of periods in years for calculations.

    Returns:
    - latest_data (pd.DataFrame): DataFrame containing the latest data row with calculated metrics.
    - regions (List[str]): List of unique regions extracted from the data.
    - latest_date (datetime): The most recent date in the data.
    - full_data (pd.DataFrame): The complete processed DataFrame with all data.
    """
    try:
        # Read the header rows
        header_rows = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
        data = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=9, header=None)
        
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

    if data is not None:
        # Construct the headers
        headers = []
        for col in range(header_rows.shape[1]):
            # For the date column
            if col == 0:
                headers.append('Date')
                continue

            # Collect the header components
            cell = header_rows.iloc[0, col]
            if pd.isna(cell):
                headers.append(f'Unknown_{col}')
                continue
            parts = [part.strip() for part in str(cell).split(';') if part.strip()]
            if len(parts) >=3:
                metric_type = parts[0]  # e.g., 'Index Numbers'
                metric = parts[1]        # e.g., 'All groups CPI'
                region = parts[2]        # e.g., 'Sydney'
            else:
                headers.append(f'Unknown_{col}')
                continue

            # Define suffix based on metric_type
            if 'Index Numbers' in metric_type:
                suffix = 'CPI'
            elif 'Percentage Change from Corresponding Quarter of Previous Year' in metric_type:
                suffix = 'PctChange_Y'
            elif 'Percentage Change from Previous Period' in metric_type:
                suffix = 'PctChange_P'
            else:
                suffix = metric_type.replace(' ', '_')
            column_name = f"{region}_{suffix}"
            headers.append(column_name)
        
        data.columns = headers
        
        # Convert the 'Date' column to datetime
        data['Date'] = pd.to_datetime(data['Date'], format='%b-%Y', errors='coerce')
        
        # Drop rows where date is NaT
        data = data.dropna(subset=['Date'])
        
        # Convert all other columns to numeric
        for col in data.columns:
            if col != 'Date':
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Set date as index
        data.set_index('Date', inplace=True)
        data.sort_index(inplace=True)
        
        # Extract unique regions
        regions = set()
        for col in data.columns:
            if col.endswith('_CPI'):
                region = col[:-4]  # Remove '_CPI'
                regions.add(region)
        
        regions = sorted(list(regions))
        
        # Define periods here for reuse
        if selected_periods is not None:
            periods = selected_periods
        else:
            periods = [1, 2, 5, 10, 15]  # Default periods

        latest_date = data.index.max()
        
        # Calculate additional metrics correctly
        for region in regions:
            cpi_col = f"{region}_CPI"
            if cpi_col in data.columns:
                # Calculate cumulative inflation over selected periods based on the latest date
                for n in periods:
                    start_date = latest_date - pd.DateOffset(years=n)
                    if start_date in data.index:
                        base_value = data.loc[start_date, cpi_col]
                    else:
                        # If exact start_date is not available, find the closest earlier date
                        base_date = data.index[data.index <= start_date].max()
                        if pd.isna(base_date):
                            data.at[latest_date, f"{region}_{n}Y_Cumulative"] = np.nan
                            continue
                        base_value = data.loc[base_date, cpi_col]
                    
                    current_value = data.loc[latest_date, cpi_col]
                    cumulative_inf = ((current_value - base_value) / base_value) * 100
                    data.at[latest_date, f"{region}_{n}Y_Cumulative"] = cumulative_inf
                
                # Quarterly inflation rate (latest)
                data.at[latest_date, f"{region}_Quarterly_Inflation"] = data[cpi_col].pct_change().iloc[-1] * 100
                
                # Annual inflation rate (latest)
                pct_change_y_col = f"{region}_PctChange_Y"
                if pct_change_y_col in data.columns:
                    data.at[latest_date, f"{region}_Annual_Inflation"] = data[pct_change_y_col].iloc[-1]
                else:
                    # Calculate it from CPI
                    data.at[latest_date, f"{region}_Annual_Inflation"] = data[cpi_col].pct_change(periods=12).iloc[-1] * 100
                
                # Purchasing power calculations
                for n in periods:
                    cum_col = f"{region}_{n}Y_Cumulative"
                    if cum_col in data.columns:
                        cum_inf = data.at[latest_date, cum_col]
                        if not pd.isna(cum_inf):
                            pp_decline = (cum_inf / (100 + cum_inf)) * 100
                            data.at[latest_date, f"{region}_{n}Y_PP_Decline"] = pp_decline
                        else:
                            data.at[latest_date, f"{region}_{n}Y_PP_Decline"] = np.nan
        
        # Keep only the latest row for cumulative metrics
        latest_data = data.loc[[latest_date]]
        
        return latest_data, regions, latest_date, data

def calculate_average_inflation(full_data: pd.DataFrame, reference_region: str, years: int) -> float:
    """
    Calculate the average annual inflation rate over the past 'years' for a given region.

    Parameters:
    - full_data (pd.DataFrame): DataFrame containing CPI data with Date as index.
    - reference_region (str): Region to calculate average inflation for.
    - years (int): Number of past years to consider.

    Returns:
    - avg_inflation (float): Average annual inflation rate in percentage.
    """
    try:
        cpi_col = f"{reference_region}_CPI"
        if cpi_col not in full_data.columns:
            raise Exception(f"CPI data for the reference region '{reference_region}' is not available.")
        
        latest_date = full_data.index.max()
        start_date = latest_date - pd.DateOffset(years=years)
        relevant_data = full_data[(full_data.index > start_date) & (full_data.index <= latest_date)][cpi_col]
        
        if len(relevant_data) < 13:  # At least two years of data (12 months)
            raise Exception(f"Not enough data to calculate average inflation over the past {years} years.")
        
        # Calculate year-over-year percentage changes
        yoy_changes = relevant_data.pct_change(periods=12) * 100  # Assuming monthly data
        avg_inflation = yoy_changes.mean()
        
        if np.isnan(avg_inflation):
            raise Exception(f"Average inflation calculation resulted in NaN for region '{reference_region}'.")
        
        return avg_inflation
    
    except Exception as e:
        raise Exception(f"Error calculating average inflation: {str(e)}")

def calculate_future_value(
    current_amount: float,
    monthly_contribution: float,
    annual_inflation: float,
    years: int
) -> float:
    """
    Calculate the future value of a deposit considering monthly contributions and annual inflation.

    Parameters:
    - current_amount (float): The initial amount.
    - monthly_contribution (float): The monthly contribution.
    - annual_inflation (float): The annual inflation rate in percentage.
    - years (int): Number of years.

    Returns:
    - future_value (float): The future value adjusted for inflation.
    """
    months = years * 12
    monthly_inflation = annual_inflation / 100 / 12
    future_value = current_amount * ((1 + monthly_inflation) ** months)
    for m in range(1, months + 1):
        future_value += monthly_contribution * ((1 + monthly_inflation) ** (months - m))
    return future_value

def calculate_required_monthly_addition(
    target_amount: float,
    current_amount: float,
    annual_inflation: float,
    years: int
) -> float:
    """
    Calculate the required monthly contribution to reach a target amount considering annual inflation.

    Parameters:
    - target_amount (float): The desired target amount.
    - current_amount (float): The current amount saved.
    - annual_inflation (float): The annual inflation rate in percentage.
    - years (int): Number of years.

    Returns:
    - required_monthly (float): The required monthly contribution.
    """
    months = years * 12
    monthly_inflation = annual_inflation / 100 / 12
    if monthly_inflation == 0:
        return (target_amount - current_amount) / months
    required = (target_amount - current_amount * ((1 + monthly_inflation) ** months)) / (
        ((1 + monthly_inflation) ** months - 1) / monthly_inflation)
    return required

def calculate_real_debt(
    full_data: pd.DataFrame,
    loan_amount: float,
    loan_term_years: int,
    start_date: datetime,
    end_date: datetime,
    average_inflation_years: int = 5,  # Number of past years to calculate average inflation
    annual_interest_rate: float = 3.5,
    reference_region: str = 'Sydney'
) -> pd.DataFrame:
    """
    Calculate the real value of the debt over time considering inflation.

    Parameters:
    - full_data (pd.DataFrame): DataFrame containing CPI data with Date as index.
    - loan_amount (float): Total loan amount in AUD.
    - loan_term_years (int): Loan term in years.
    - start_date (datetime): The date when the loan started.
    - end_date (datetime): The current date.
    - average_inflation_years (int, optional): Number of past years to calculate average inflation. Default is 5.
    - annual_interest_rate (float, optional): Annual interest rate as a percentage. Default is 3.5%.
    - reference_region (str, optional): Region to use for CPI data. Default is 'Sydney'.

    Returns:
    - debt_df (pd.DataFrame): DataFrame with Real Debt over time.
    """
    try:
        # Calculate average annual inflation rate up to start_date
        inflation_data = full_data[full_data.index <= start_date]
        if len(inflation_data) < average_inflation_years * 12 + 1:
            raise Exception(f"Not enough data to calculate average inflation over the past {average_inflation_years} years up to {start_date.strftime('%b-%Y')}.")

        avg_annual_inflation = calculate_average_inflation(
            full_data=inflation_data,
            reference_region=reference_region,
            years=average_inflation_years
        )

        # Generate a date range from start_date to end_date
        loan_dates = pd.date_range(start=start_date, end=end_date, freq='MS')  # Monthly Start

        # Initialize DataFrame to store debt over time
        debt_df = pd.DataFrame(index=loan_dates)
        debt_df['Real Debt (AUD)'] = np.nan
        debt_df['Cumulative Inflation (%)'] = np.nan

        # Since nominal debt is constant, real debt decreases due to inflation
        cumulative_inflation = 1.0  # Starts at 1 (no inflation)

        for date in loan_dates:
            # Apply monthly inflation
            monthly_inflation = (1 + avg_annual_inflation / 100) ** (1/12) - 1  # Convert annual to monthly
            cumulative_inflation *= (1 + monthly_inflation)  # Compound inflation

            # Update real debt based on cumulative inflation
            real_debt = loan_amount / cumulative_inflation

            # Record values
            debt_df.at[date, 'Real Debt (AUD)'] = real_debt
            debt_df.at[date, 'Cumulative Inflation (%)'] = (cumulative_inflation - 1) * 100

        return debt_df

    except Exception as e:
        raise Exception(f"Error calculating real debt: {str(e)}")
