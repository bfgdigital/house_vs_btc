# inflation_analysis.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Function to load and process CPI data
def load_and_process_cpi(file_path='data/640101.xlsx', sheet_name='Data1'):
    """Load and process CPI data from Excel file with multi-row headers"""
    try:
        # Read the first 8 rows for header processing
        header_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=8)
        
        # Process the first row which contains the metric descriptions
        headers = []
        for col in header_df.columns:
            cell = header_df.iloc[0, col]
            if pd.isna(cell):
                headers.append('Unknown')
                continue
                
            parts = [part.strip() for part in str(cell).split(';') if part.strip()]
            if len(parts) >= 3:
                metric_type = parts[0].strip()  # Index Numbers, Percentage Change, etc.
                metric = parts[1].strip()  # All groups CPI
                region = parts[2].strip()  # Sydney, Melbourne, etc.
                
                # Define column name based on metric type
                if 'Index Numbers' in metric_type:
                    suffix = 'CPI'
                elif 'Corresponding Quarter of Previous Year' in metric_type:
                    suffix = 'PctChange_Y'
                elif 'Previous Period' in metric_type:
                    suffix = 'PctChange_P'
                else:
                    suffix = metric_type.replace(' ', '_')
                
                column_name = f"{region}_{suffix}"
            else:
                column_name = f"Unknown_{col}"
            
            headers.append(column_name)
        
        # Read the actual data starting from row 9 (after headers)
        data = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=9, header=None)
        data.columns = headers
        
        # Convert the first column to datetime
        date_column = data.columns[0]
        data[date_column] = pd.to_datetime(data[date_column], format='%b-%Y', errors='coerce')
        
        # Drop rows where date is NaT
        data = data.dropna(subset=[date_column])
        
        # Convert all numeric columns
        for col in data.columns:
            if col != date_column:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Set date as index
        data.set_index(date_column, inplace=True)
        data.sort_index(inplace=True)
        
        # Extract unique regions (removing suffixes)
        regions = set()
        for col in data.columns:
            if '_CPI' in col:
                region = col.replace('_CPI', '')
                regions.add(region)
        
        regions = sorted(list(regions))
        
        # Calculate additional metrics
        for region in regions:
            cpi_col = f"{region}_CPI"
            if cpi_col in data.columns:
                # Quarterly inflation rate
                data[f"{region}_Quarterly"] = data[cpi_col].pct_change() * 100
                
                # Annualized rate
                data[f"{region}_Annualised"] = ((1 + data[f"{region}_Quarterly"] / 100) ** 4 - 1) * 100
                
                # Cumulative calculations for selected periods
                for period in [1, 2, 5, 10, 15]:
                    periods = period * 4  # Quarterly data
                    data[f"{region}_{period}Y_Cumulative"] = (data[cpi_col] / data[cpi_col].shift(periods) - 1) * 100
                
                # All-time cumulative
                data[f"{region}_AllTime"] = (data[cpi_col] / data[cpi_col].iloc[0] - 1) * 100
                
                # Purchasing power calculations
                data[f"{region}_PurchasingPower"] = (data[cpi_col].iloc[0] / data[cpi_col]) * 100  # Base 100%
        
        latest_date = data.index.max()
        latest_data = data.loc[latest_date]
        
        return data, regions, latest_date, data
        
    except Exception as e:
        raise Exception(f"Error processing CPI data: {str(e)}")

# Financial calculation functions
def calculate_future_value(current_amount, monthly_contribution, annual_inflation, years):
    """
    Calculate the future value of savings with monthly contributions and annual inflation.
    """
    future_value = current_amount
    monthly_inflation_rate = (1 + annual_inflation / 100) ** (1/12) - 1
    months = years * 12
    for _ in range(int(months)):
        future_value = future_value * (1 + monthly_inflation_rate) + monthly_contribution
    return future_value

def calculate_required_monthly_addition(target_amount, current_amount, annual_inflation, years):
    """
    Calculate the required monthly addition to reach a target amount, considering annual inflation.
    """
    monthly_inflation_rate = (1 + annual_inflation / 100) ** (1/12) - 1
    months = years * 12
    # Future Value of an Annuity formula
    r = monthly_inflation_rate
    n = months
    FV = target_amount
    Pmt = (FV - current_amount * (1 + r) ** n) * r / ((1 + r) ** n - 1)
    return Pmt

def calculate_real_debt(full_data, loan_amount, loan_term_years, start_date, end_date, reference_region):
    """
    Calculate the real value of the debt over time, adjusted for inflation.
    """
    cpi_col = f"{reference_region}_CPI"
    if cpi_col not in full_data.columns:
        raise Exception(f"CPI data for {reference_region} is not available.")
    
    data = full_data.loc[start_date:end_date]
    dates = data.index
    n_months = len(dates)
    debt_remaining = loan_amount
    real_debt_values = []
    cumulative_inflation = []
    cpi_start = data[cpi_col].iloc[0]
    for i in range(n_months):
        # Adjust for inflation
        cpi_current = data[cpi_col].iloc[i]
        inflation_factor = cpi_current / cpi_start
        real_debt = debt_remaining / inflation_factor
        real_debt_values.append(real_debt)
        
        # Cumulative inflation
        cumulative_inflation.append((inflation_factor - 1) * 100)
    
    debt_df = pd.DataFrame({
        'Real Debt (AUD)': real_debt_values,
        'Cumulative Inflation (%)': cumulative_inflation
    }, index=dates)
    return debt_df

# Plotting functions (combined and improved)
def plot_purchasing_power_decline(full_data, selected_regions, timeframe_label, date_range=None):
    """Plot the purchasing power decline over the specified time period with dual y-axes."""
    fig = go.Figure()
    
    # Filter data based on date_range if provided
    if date_range:
        data = full_data[(full_data.index >= date_range[0]) & (full_data.index <= date_range[1])]
    else:
        data = full_data.copy()
    
    for region in selected_regions:
        pp_col = f"{region}_PurchasingPower"
        if pp_col in data.columns:
            pp_percent = data[pp_col]
            pp_dollars = pp_percent / 100  # $1 adjusted for purchasing power
            
            # Add percentage trace
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=pp_percent,
                    mode='lines',
                    name=f'{region} Purchasing Power (%)',
                    yaxis='y1'
                )
            )
            
            # Add dollar trace
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=pp_dollars,
                    mode='lines',
                    name=f'{region} Purchasing Power ($1)',
                    yaxis='y2'
                )
            )
    
    # Create dual y-axes
    fig.update_layout(
        title=f'Purchasing Power Decline Over {timeframe_label}',
        xaxis_title='Date',
        yaxis=dict(
            title='Purchasing Power (%)',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title='Purchasing Power ($1)',
            titlefont=dict(color='orange'),
            tickfont=dict(color='orange'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=600,
        legend_title_text='Region',
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_cumulative_inflation(full_data, selected_regions, timeframe_label, date_range=None):
    """Plot cumulative inflation over the specified time period."""
    fig = go.Figure()
    
    # Filter data based on date_range if provided
    if date_range:
        data = full_data[(full_data.index >= date_range[0]) & (full_data.index <= date_range[1])]
    else:
        data = full_data.copy()
    
    for region in selected_regions:
        all_time_col = f"{region}_AllTime"
        if all_time_col in data.columns:
            cum_inf = data[all_time_col]
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=cum_inf,
                    mode='lines',
                    name=f'{region} Cumulative Inflation (%)'
                )
            )
    
    fig.update_layout(
        title=f'Cumulative Inflation Over {timeframe_label}',
        xaxis_title='Date',
        yaxis_title='Cumulative Inflation (%)',
        hovermode='x unified',
        height=600,
        legend_title_text='Region',
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_savings_journey(full_data, selected_regions, monthly_contribution, deposit_target, timeframe_label, date_range=None):
    """Plot the savings journey over the specified time period."""
    fig = go.Figure()
    
    # Filter data based on date_range if provided
    if date_range:
        data = full_data[(full_data.index >= date_range[0]) & (full_data.index <= date_range[1])]
    else:
        data = full_data.copy()
    
    for region in selected_regions:
        cpi_col = f"{region}_CPI"
        if cpi_col in data.columns:
            dates = data.index
            n_months = len(dates)
            actual_savings = []
            required_savings = []
            required_monthly_savings = []
            current_savings = 0
            required = deposit_target
            for i in range(n_months):
                if i == 0:
                    monthly_inflation = 0
                else:
                    cpi_prev = data[cpi_col].iloc[i - 1]
                    cpi_current = data[cpi_col].iloc[i]
                    monthly_inflation = (cpi_current - cpi_prev) / cpi_prev
                current_savings = current_savings * (1 + monthly_inflation) + monthly_contribution
                actual_savings.append(current_savings)
                
                # Update required savings to beat inflation
                required = required * (1 + monthly_inflation)
                required_savings.append(required)
                
                # Calculate required monthly savings to reach the goal
                remaining_months = n_months - i
                if remaining_months > 0 and monthly_inflation != 0:
                    future_value_factor = ((1 + monthly_inflation) ** remaining_months - 1) / monthly_inflation
                    required_monthly = (required - current_savings * (1 + monthly_inflation) ** remaining_months) / future_value_factor
                else:
                    required_monthly = required / remaining_months if remaining_months > 0 else 0
                required_monthly_savings.append(required_monthly)
                
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=actual_savings,
                    mode='lines',
                    name=f'{region} Actual Savings'
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=required_savings,
                    mode='lines',
                    name=f'{region} Required Savings',
                    line=dict(dash='dash')
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=required_monthly_savings,
                    mode='lines',
                    name=f'{region} Required Monthly Contribution',
                    line=dict(dash='dot')
                )
            )
    
    fig.update_layout(
        title=f'Savings Journey Over {timeframe_label}',
        xaxis_title='Date',
        yaxis_title='Amount (AUD)',
        hovermode='x unified',
        height=600,
        legend_title_text='Savings Metrics',
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_debt_reduction(debt_df, timeframe_label):
    """
    Plot the real debt over time.
    """
    fig = go.Figure()

    # Real Debt Trace
    fig.add_trace(
        go.Scatter(
            x=debt_df.index,
            y=debt_df['Real Debt (AUD)'],
            mode='lines',
            name='Real Debt (Adjusted for Inflation)',
            line=dict(color='green', width=2)
        )
    )

    fig.update_layout(
        title=f'Real Debt Reduction Over {timeframe_label}',
        xaxis_title='Date',
        yaxis_title='Real Debt (AUD)',
        hovermode='x unified',
        height=600,
        legend_title_text='Debt Metrics',
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_recent_growth(full_data, selected_regions):
    """Plot recent quarterly growth rates for selected regions."""
    recent_growth = {}
    for region in selected_regions:
        quarterly_col = f"{region}_Quarterly"
        if quarterly_col in full_data.columns:
            recent_growth[region] = full_data[quarterly_col].tail(8)
    if not recent_growth:
        return go.Figure()
    recent_df = pd.DataFrame(recent_growth)
    recent_df.index = [f"{idx.year}-Q{idx.quarter}" for idx in recent_df.index]
    fig = px.line(recent_df, x=recent_df.index, y=recent_df.columns, markers=True,
                  title='Recent Quarterly Inflation Trend')
    fig.update_layout(
        xaxis_title='Quarter',
        yaxis_title='Inflation Rate (%)',
        hovermode='x unified',
        height=400,
        legend_title_text='Region',
        font=dict(
            family="sans-serif"
        )
    )
    return fig

# Streamlit App
st.set_page_config(page_title="Australian Inflation Analysis", layout="wide")
st.title("Understanding Inflation's Impact on Your Finances")

# Sidebar for User Inputs
st.sidebar.header('Financial Planning Inputs')

# Load Data
try:
    # Load CPI data
    full_data, regions, latest_date, latest_data = load_and_process_cpi(
        'data/640101.xlsx',
        sheet_name='Data1'
    )

    if full_data.empty:
        st.error("No data available. Please check the data file and try again.")
    else:
        st.sidebar.success(f"Data loaded successfully! Latest date: {latest_date.strftime('%B %Y')}")

        # Interactive Region Selection
        selected_regions = st.sidebar.multiselect(
            'Choose one or more regions:',
            options=regions,
            default=regions
        )

        if not selected_regions:
            st.sidebar.warning("Please select at least one region to proceed.")

        # Section 1: Purchasing Power Decline
        st.header("1. The Shrinking Value of Your Dollar")
        st.markdown("""
        Ever felt like your money doesn't go as far as it used to? That's inflation at work. This section shows how the value of a single dollar has declined over time due to rising prices.
        """)

        timeframe_options = ["All Time", "Selected Period"]
        selected_timeframe = st.selectbox(
            "Choose a timeframe for analysis:",
            options=timeframe_options
        )

        if selected_timeframe == "All Time":
            timeframe_label = "All Time"
            date_range = None  # Entire dataset
        else:
            # Time period selection in sidebar
            selected_years = st.sidebar.selectbox(
                'Select number of years for analysis:',
                options=[1, 2, 5, 10, 15],
                index=2,  # Default to 5 years
                format_func=lambda x: f"{x} Years"
            )
            selected_start_date = latest_date - pd.DateOffset(years=selected_years)
            timeframe_label = f"Last {selected_years} Years"
            date_range = (selected_start_date, latest_date)

        pp_decline_fig = plot_purchasing_power_decline(
            full_data=full_data,
            selected_regions=selected_regions,
            timeframe_label=timeframe_label,
            date_range=date_range
        )
        cum_inflation_fig = plot_cumulative_inflation(
            full_data=full_data,
            selected_regions=selected_regions,
            timeframe_label=timeframe_label,
            date_range=date_range
        )

        # Display Charts
        st.plotly_chart(pp_decline_fig, use_container_width=True)
        st.plotly_chart(cum_inflation_fig, use_container_width=True)

        st.markdown("""
        **What's the takeaway?** Simply put, the longer you hold onto cash, the less it's worth. That's why it's important to consider how inflation affects your savings and purchasing power over time.
        """)

        # Section 2: Inflation Headwinds While Saving for a Deposit
        st.header("2. Battling Inflation While Saving for a House")

        st.markdown("""
        Saving for a house deposit? Inflation can make that goal seem like a moving target. Here's how much you need to save each month to stay on track.
        """)

        # Savings Inputs
        deposit_target = st.sidebar.number_input(
            'Deposit Target Amount (in AUD)',
            min_value=0.0,
            value=200000.0,
            step=10000.0,
            format="%.2f"
        )
        monthly_contribution = st.sidebar.number_input(
            'Monthly Contribution (in AUD)',
            min_value=0.0,
            value=1000.0,
            step=100.0,
            format="%.2f"
        )

        if selected_timeframe == "All Time":
            savings_timeframe = st.sidebar.number_input(
                'Savings Period (in Years)',
                min_value=1,
                max_value=50,
                value=30,
                step=1
            )
            selected_start_date = latest_date - pd.DateOffset(years=savings_timeframe)
            timeframe_label = f"{savings_timeframe} Years"
            date_range = (selected_start_date, latest_date)
        else:
            savings_timeframe = selected_years
            timeframe_label = f"{selected_years} Years"
            date_range = (selected_start_date, latest_date)

        savings_fig = plot_savings_journey(
            full_data=full_data,
            selected_regions=selected_regions,
            monthly_contribution=monthly_contribution,
            deposit_target=deposit_target,
            timeframe_label=timeframe_label,
            date_range=date_range
        )

        st.plotly_chart(savings_fig, use_container_width=True)

        st.markdown("""
        **So, what's happening here?** Inflation means you'll need to save more than you initially thought. The dashed lines show how much your savings goal increases over time, and the dotted lines indicate the required monthly savings to keep up with inflation.
        """)

        # Section 3: Inflation's Effect on Your Debt
        st.header("3. Inflation Reducing Your Debt in Real Terms")

        st.markdown("""
        While inflation can be a hurdle when saving, it can actually work in your favour when it comes to debt. Over time, inflation reduces the 'real' value of what you owe.
        """)

        # Debt Management Inputs
        loan_amount = st.sidebar.number_input(
            'Loan Amount (in AUD)',
            min_value=0.0,
            value=800000.0,
            step=10000.0,
            format="%.2f"
        )
        loan_term_years = st.sidebar.number_input(
            'Loan Term (in Years)',
            min_value=1,
            max_value=50,
            value=30,
            step=1
        )
        reference_region = st.sidebar.selectbox(
            'Select Region for Debt Calculation:',
            options=regions,
            index=regions.index('Sydney') if 'Sydney' in regions else 0
        )

        # Calculate Real Debt
        loan_start_date = latest_date - pd.DateOffset(years=loan_term_years)
        if selected_timeframe == "All Time":
            timeframe_label = f"{loan_term_years} Years"
            date_range = (loan_start_date, latest_date)
        else:
            timeframe_label = f"{selected_years} Years"
            date_range = (latest_date - pd.DateOffset(years=selected_years), latest_date)

        debt_df = calculate_real_debt(
            full_data=full_data,
            loan_amount=loan_amount,
            loan_term_years=loan_term_years,
            start_date=date_range[0],
            end_date=date_range[1],
            reference_region=reference_region
        )

        debt_fig = plot_debt_reduction(
            debt_df=debt_df,
            timeframe_label=timeframe_label
        )
        st.plotly_chart(debt_fig, use_container_width=True)

        st.markdown("""
        **What's the benefit?** As prices rise, the 'real' value of your fixed debt decreases. That means the amount you owe becomes less significant compared to the overall economy.
        """)

        # Recent Quarterly Growth Rates
        st.header("4. Recent Inflation Trends")
        st.markdown("""
        Curious about how inflation's been tracking lately? Here's a snapshot of the recent quarterly inflation rates.
        """)
        st.plotly_chart(plot_recent_growth(full_data, selected_regions), use_container_width=True)

        # Conclusion
        st.header("5. Wrapping It Up")
        st.markdown('''
        Inflation is a double-edged sword. It can erode your savings and make financial goals seem harder to reach, but it can also lessen the burden of debt over time. Understanding how it affects your finances is key to making smart money moves.

        **Remember:**
        - **Stay Ahead of Inflation:** Consider investment options that outpace inflation to protect your savings.
        - **Leverage Debt Wisely:** Fixed-rate loans can be beneficial in an inflationary environment.
        - **Keep an Eye on Trends:** Regularly monitoring inflation can help you adjust your financial strategies.

        By staying informed and proactive, you can navigate the ups and downs of the economy and work towards your financial goals with confidence.
        ''')

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Please check the data file and your inputs, then try again.")
