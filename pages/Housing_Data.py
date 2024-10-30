import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Load and process data function
def load_and_process_excel(file_path='data/643201.xlsx', sheet_name='Data1'):
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Find columns containing mean price data
        mean_price_cols = [col for col in df.columns if 'Mean price of residential dwellings' in str(col)]
        
        # Get the dates from the first column
        dates = df.iloc[9:, 0]  # Skip metadata rows
        
        # Create a new DataFrame with dates as index and states as columns
        states = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']
        processed_df = pd.DataFrame(index=pd.to_datetime(dates), columns=states)
        
        # Map full names to abbreviations
        state_map = {
            'New South Wales': 'NSW',
            'Victoria': 'VIC',
            'Queensland': 'QLD',
            'South Australia': 'SA',
            'Western Australia': 'WA',
            'Tasmania': 'TAS',
            'Northern Territory': 'NT',
            'Australian Capital Territory': 'ACT'
        }
        
        # Fill the DataFrame with values
        for col in mean_price_cols:
            for state_full, state_abbr in state_map.items():
                if state_full in col:
                    values = df.iloc[9:][col].values  # Skip metadata rows
                    processed_df[state_abbr] = pd.to_numeric(values, errors='coerce') * 1000  # Convert from $'000 to actual values
                    break
        
        return processed_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Growth calculations and analytics
def calculate_growth_rates(df, period='Y'):
    """Calculate growth rates for different periods ('Y' for annual, 'Q' for quarterly')"""
    if period == 'Y':
        period_df = df.resample('Y').last()
    else:
        period_df = df.copy()
    
    growth_df = period_df.pct_change() * 100
    return growth_df

def create_growth_summary_table(df):
    """Create a comprehensive growth summary table with both annual and quarterly data"""
    # Calculate annual and quarterly growth rates
    annual_growth = calculate_growth_rates(df, 'Y')
    quarterly_growth = calculate_growth_rates(df, 'Q')
    
    # Create summary statistics
    summary_data = {
        'Annual Average Growth (%)': annual_growth.mean(),
        'Annual Median Growth (%)': annual_growth.median(),
        'Quarterly Average Growth (%)': quarterly_growth.mean(),
        'Quarterly Median Growth (%)': quarterly_growth.median(),
        'Highest Annual Growth (%)': annual_growth.max(),
        'Lowest Annual Growth (%)': annual_growth.min(),
        'Highest Quarterly Growth (%)': quarterly_growth.max(),
        'Lowest Quarterly Growth (%)': quarterly_growth.min(),
    }
    
    return pd.DataFrame(summary_data).round(2)

def get_annual_growth_table(df):
    """Create a table of annual growth rates"""
    # Ensure we only get one value per year by using end of year
    annual_df = df.resample('Y').last()
    growth_df = annual_df.pct_change() * 100
    # Create unique index using year
    growth_df.index = growth_df.index.year
    # Sort index to ensure correct ordering
    return growth_df.sort_index().round(2)

def get_quarterly_growth_table(df):
    """Create a table of quarterly growth rates"""
    growth_df = df.pct_change() * 100
    # Create unique index using year and quarter
    growth_df.index = [f"{idx.year}-Q{idx.quarter}" for idx in growth_df.index]
    # Get last 8 quarters and ensure unique index
    return growth_df.tail(8).round(2)

def plot_price_timeline(df):
    fig = go.Figure()
    
    for column in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[column],
                name=column,
                mode='lines'
            )
        )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Price ($)',
        hovermode='x unified',
        height=600,
        showlegend=True,
        legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
        margin={'t': 30},  # Reduce top margin since we're using st.header
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_recent_growth(df):
    recent = calculate_growth_rates(df, 'Q').tail(8)
    recent.index = [f"{idx.year}-Q{idx.quarter}" for idx in recent.index]
    fig = go.Figure()
    
    for column in recent.columns:
        fig.add_trace(
            go.Scatter(
                x=recent.index,
                y=recent[column],
                name=column,
                mode='lines+markers'
            )
        )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Growth Rate (%)',
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
        margin={'t': 30},
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_cumulative_growth(df):
    cumulative_growth = (df / df.iloc[0] - 1) * 100
    fig = px.line(cumulative_growth, x=cumulative_growth.index, y=cumulative_growth.columns)
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Cumulative Growth (%)',
        title='Cumulative Growth of Housing Prices Over Time',
        hovermode='x unified',
        height=600,
        legend_title_text='State/Territory',
        font=dict(
            family="sans-serif"
        )
    )
    return fig

# Streamlit App
st.set_page_config(page_title="Australian Housing Market Analysis", layout="centered") 
st.title('Australian Residential Housing Market Analysis')

# Introduction
st.header('1. Introduction')
st.markdown('''
Understanding the housing market is crucial for policymakers, investors, and the general public. This analysis delves into historical housing prices to shed light on market trends across Australia.

**Key Objectives:**
- Understand long-term trends in housing prices.
- Compare growth rates between different states and territories.
- Identify recent patterns and anomalies in the market.
''')

# Data Source Information
st.subheader('Data Source')
st.markdown('''
The housing market data is sourced from the Australian Bureau of Statistics (ABS), specifically from [ABS Total Value of Dwellings Report](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings). This dataset contains historical mean price data of residential dwellings across Australian states and territories, reported quarterly.
''')

# Load Data
try:
    df = load_and_process_excel('data/643201.xlsx')

    if df.empty:
        st.error("No data available. Please check the data file and try again.")
    else:
        st.success("Data loaded successfully!")

        # Interactive State Selection
        st.header('2. Select States/Territories to Analyze')
        selected_states = st.multiselect('Choose one or more states/territories:', options=df.columns.tolist(), default=df.columns.tolist())
        filtered_df = df[selected_states]

        # Overall Housing Price Analysis
        st.header('3. Historical Housing Prices')
        st.markdown('''
This section provides an overview of the historical housing prices across different Australian states and territories. The data is presented as a timeline to help identify trends and patterns over time. This analysis helps to understand how the housing market has evolved across different regions.
''')

        st.subheader('3.1. Housing Price Timeline')
        st.markdown('''
The following plot shows the mean residential dwelling prices for each selected state and territory in Australia over time. This allows you to observe the growth, stability, or decline in housing prices across different regions.
''')
        st.plotly_chart(plot_price_timeline(filtered_df), use_container_width=True)

        st.subheader('3.2. Cumulative Growth Since Start Date')
        st.markdown('''
This plot illustrates the cumulative growth in housing prices since the earliest date in the dataset for the selected regions. It provides a comparative view of how much each region's housing market has grown over time.
''')
        st.plotly_chart(plot_cumulative_growth(filtered_df), use_container_width=True)

        st.subheader('3.3. Current House Prices')
        st.markdown('''
The metrics below represent the most recent average prices of residential dwellings in each selected state and territory. This information is crucial for understanding the current market status.
''')

        current_prices = filtered_df.iloc[-1].round(2)
        for state, price in current_prices.items():
            st.metric(label=state, value=f"${price:,.2f}")

        # Growth Analysis
        st.header('4. Growth Analysis')
        st.markdown('''
In this section, we examine the growth rates of housing prices to understand both annual and quarterly changes. By comparing these rates, we can gain insights into the volatility and long-term trends in the housing market.
''')

        # Annual Growth Rates Table
        st.subheader('4.1. Annual Growth Rates (%)')
        st.markdown('''
The table below presents the annual growth rates of residential dwelling prices for each selected state and territory. This helps to understand the year-on-year changes in housing prices, providing insight into longer-term trends.
''')
        annual_growth = get_annual_growth_table(filtered_df)
        st.dataframe(annual_growth.style.format("{:.2f}%")
                     .highlight_max(axis=1, color='lightgreen')
                     .highlight_min(axis=1, color='salmon'))

        # Quarterly Growth Rates Table
        st.subheader('4.2. Recent Quarterly Growth Rates (%)')
        st.markdown('''
The table below shows the growth rates for the most recent eight quarters. This analysis is useful for observing shorter-term changes and fluctuations in the housing market, providing a more granular view compared to the annual rates.
''')
        quarterly_growth = get_quarterly_growth_table(filtered_df)
        st.dataframe(quarterly_growth.style.format("{:.2f}%")
                     .highlight_max(axis=1, color='lightgreen')
                     .highlight_min(axis=1, color='salmon'))

        # Recent Growth Rates Plot
        st.subheader('4.3. Recent Quarterly Growth Trend')
        st.markdown('''
The following plot visualizes the recent quarterly growth trends for each selected state and territory. This helps to identify any short-term patterns or anomalies in the housing market.
''')
        st.plotly_chart(plot_recent_growth(filtered_df), use_container_width=True)

        # Growth Summary Statistics
        st.header('5. Summary Statistics of Growth Rates')
        st.markdown('''
This table summarizes key statistics regarding the annual and quarterly growth rates of housing prices. It includes averages, medians, and the highest and lowest growth rates observed, providing a comprehensive overview of the growth dynamics in the housing market.
''')
        growth_summary = create_growth_summary_table(filtered_df)
        st.dataframe(growth_summary.style.format("{:.2f}%"))

        # Conclusion
        st.header('6. Conclusion')
        st.markdown('''
The Australian housing market exhibits diverse trends across different states and territories. By analyzing both long-term and short-term growth rates, we gain valuable insights into market dynamics that can inform investment decisions and policy-making.

**Key Takeaways:**
- There are significant differences in housing price growth between regions.
- Recent quarterly trends may indicate changing market conditions.
- Continuous monitoring of growth rates is essential for staying informed.

**Future Outlook:**
- Factors such as economic policies, population growth, and global events can influence the housing market.
- Further analysis could include adjusting for inflation or exploring correlations with other economic indicators.
''')
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Please check the data file and try again.")
