import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Load BTC data function
def load_btc_data():
    try:
        btc_aud = yf.download('BTC-AUD', start='2011-09-01', end=datetime.today().strftime('%Y-%m-%d'), interval='1d')
        btc_aud.index = pd.to_datetime(btc_aud.index.date)
        quarterly_data = btc_aud['Close'].resample('QE').last()
        processed_df = pd.DataFrame({'BTC': quarterly_data.values.flatten()}, index=quarterly_data.index)
        return processed_df
    except Exception as e:
        st.error(f"Error loading BTC data: {str(e)}")
        return pd.DataFrame()

# Growth calculations and analytics
def calculate_growth_rates(df, period='YE'):
    """Calculate growth rates for different periods ('YE' for annual, 'QE' for quarterly)"""
    if period == 'YE':
        period_df = df.resample('YE').last()
    else:
        period_df = df.copy()
    
    growth_df = period_df.pct_change() * 100
    return growth_df

def create_growth_summary_table(df):
    """Create a comprehensive growth summary table with both annual and quarterly data"""
    # Calculate annual and quarterly growth rates
    annual_growth = calculate_growth_rates(df, 'YE')
    quarterly_growth = calculate_growth_rates(df, 'QE')
    
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
        'Volatility (Std Dev of Quarterly Growth)': quarterly_growth.std()
    }
    
    return pd.DataFrame(summary_data).round(2)

def get_annual_growth_table(df):
    """Create a table of annual growth rates"""
    annual_df = df.resample('YE').last()
    growth_df = annual_df.pct_change() * 100
    growth_df.index = growth_df.index.year
    return growth_df.sort_index().round(2)

def get_quarterly_growth_table(df):
    """Create a table of quarterly growth rates"""
    growth_df = df.pct_change() * 100
    growth_df.index = [f"{idx.year}-Q{idx.quarter}" for idx in growth_df.index]
    return growth_df.tail(8).round(2)

def plot_price_timeline(df):
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['BTC'],
            name='BTC',
            mode='lines'
        )
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Price (AUD)',
        hovermode='x unified',
        height=600,
        showlegend=True,
        legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
        margin={'t': 30},
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_recent_growth(df):
    recent = calculate_growth_rates(df, 'QE').tail(8)
    recent.index = [f"{idx.year}-Q{idx.quarter}" for idx in recent.index]
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=recent.index,
            y=recent['BTC'],
            name='BTC',
            mode='lines+markers'
        )
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Growth Rate (%)',
        hovermode='x unified',
        height=400,
        showlegend=False,
        margin={'t': 30},
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def plot_cumulative_growth(df):
    cumulative_growth = (df / df.iloc[0] - 1) * 100
    fig = px.line(cumulative_growth, x=cumulative_growth.index, y='BTC', title='Cumulative Growth of BTC Price Over Time')
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Cumulative Growth (%)',
        hovermode='x unified',
        height=600,
        font=dict(
            family="sans-serif"
        )
    )
    return fig

def get_price_analytics(df):
    current_price = df.iloc[-1]['BTC']
    all_time_high = df['BTC'].max()
    all_time_low = df['BTC'].min()
    price_change_last_year = (df['BTC'].pct_change(periods=4).iloc[-1] * 100)
    current_vs_ath = (current_price / all_time_high * 100)
    
    analytics = {
        'Current Price': f"${current_price:,.2f}",
        'All-Time High': f"${all_time_high:,.2f}",
        'All-Time Low': f"${all_time_low:,.2f}",
        'Price Change (Last Year)': f"{price_change_last_year:.2f}%",
        'Current Price vs ATH': f"{current_vs_ath:.2f}%"
    }
    return analytics

# Streamlit App
st.set_page_config(page_title="Bitcoin (BTC) Price Analysis in AUD", layout="centered") 
st.title('Bitcoin (BTC) Price Analysis in AUD')

# Introduction
st.header('1. Introduction')
st.markdown('''
Bitcoin, as the first and most prominent cryptocurrency, has seen significant price movements since its inception. This analysis explores the historical prices of Bitcoin in Australian Dollars (AUD) to provide insights into its market trends.

**Key Objectives:**
- Analyze long-term and short-term price trends of Bitcoin in AUD.
- Compare growth rates to understand volatility and performance.
- Present data in a way that aligns with the housing market analysis for easy comparison.
''')

# Data Source Information
st.subheader('Data Source')
st.markdown('''
The Bitcoin price data is sourced from Yahoo Finance, providing daily closing prices of Bitcoin (BTC) in Australian Dollars (AUD) from September 2011 to the present. Yahoo Finance is a reputable source for financial data, ensuring reliable historical pricing information.
''')

# Load Data
try:
    df = load_btc_data()

    if df.empty:
        st.error("No data available. Please try again later.")
    else:
        st.success("Data loaded successfully!")

        # Overall Bitcoin Price Analysis
        st.header('2. Historical Bitcoin Prices')
        st.markdown('''
This section provides an overview of the historical prices of Bitcoin in AUD. The data is presented as a timeline to help identify trends and significant price movements over time.
''')

        st.subheader('2.1. Bitcoin Price Timeline')
        st.markdown('''
The following plot shows the closing prices of Bitcoin in AUD over time. This allows you to observe the growth, volatility, or decline in Bitcoin prices since 2011.
''')
        st.plotly_chart(plot_price_timeline(df), use_container_width=True)

        st.subheader('2.2. Cumulative Growth Since Start Date')
        st.markdown('''
This plot illustrates the cumulative growth of Bitcoin's price in AUD since September 2011. It provides a visual representation of Bitcoin's overall performance over time.
''')
        st.plotly_chart(plot_cumulative_growth(df), use_container_width=True)

        st.subheader('2.3. Current Bitcoin Price')
        st.markdown('''
The metric below represents the most recent closing price of Bitcoin in AUD. This provides a snapshot of Bitcoin's current market value.
''')
        current_price = df.iloc[-1]['BTC']
        st.metric(label='BTC', value=f"${current_price:,.2f}")

        # Growth Analysis
        st.header('3. Growth Analysis')
        st.markdown('''
In this section, we examine the growth rates of Bitcoin prices to understand both annual and quarterly changes. By comparing these rates, we can gain insights into Bitcoin's volatility and long-term trends.
''')

        # Annual Growth Rates Table
        st.subheader('3.1. Annual Growth Rates (%)')
        st.markdown('''
The table below presents the annual growth rates of Bitcoin's price in AUD. This helps to understand the year-on-year changes, providing insight into longer-term trends.
''')
        annual_growth = get_annual_growth_table(df)
        st.dataframe(annual_growth.style.format("{:.2f}%")
                     .highlight_max(axis=0, color='lightgreen')
                     .highlight_min(axis=0, color='salmon'))

        # Quarterly Growth Rates Table
        st.subheader('3.2. Recent Quarterly Growth Rates (%)')
        st.markdown('''
The table below shows the growth rates for the most recent eight quarters. This analysis is useful for observing shorter-term changes and fluctuations in Bitcoin's price.
''')
        quarterly_growth = get_quarterly_growth_table(df)
        st.dataframe(quarterly_growth.style.format("{:.2f}%")
                     .highlight_max(axis=0, color='lightgreen')
                     .highlight_min(axis=0, color='salmon'))

        # Recent Growth Rates Plot
        st.subheader('3.3. Recent Quarterly Growth Trend')
        st.markdown('''
The following plot visualizes the recent quarterly growth trends of Bitcoin in AUD. This helps to identify any short-term patterns or significant movements in the market.
''')
        st.plotly_chart(plot_recent_growth(df), use_container_width=True)

        # Growth Summary Statistics
        st.header('4. Summary Statistics of Growth Rates')
        st.markdown('''
This table summarizes key statistics regarding the annual and quarterly growth rates of Bitcoin's price in AUD. It includes averages, medians, and the highest and lowest growth rates observed, providing a comprehensive overview of Bitcoin's performance.
''')
        growth_summary = create_growth_summary_table(df)
        st.dataframe(growth_summary.style.format("{:.2f}%"))

        # Price Analytics
        st.header('5. Price Analytics')
        st.markdown('''
The following metrics provide insight into the current price of Bitcoin compared to its historical highs and lows, as well as recent performance.
''')
        price_analytics = get_price_analytics(df)
        for key, value in price_analytics.items():
            st.write(f"**{key}:** {value}")

        # Conclusion
        st.header('6. Conclusion')
        st.markdown('''
The analysis of Bitcoin prices in AUD reveals significant volatility and substantial growth over time. Understanding these patterns is essential for investors and enthusiasts alike.

**Key Takeaways:**
- Bitcoin has experienced periods of extreme growth and decline, highlighting its volatile nature.
- The highest annual growth rates significantly outperform traditional assets, but so do the declines.
- Recent quarterly trends indicate ongoing fluctuations in the market.

**Future Outlook:**
- Market dynamics, regulatory changes, and global economic factors will continue to influence Bitcoin's price.
- Continuous monitoring and analysis are necessary to navigate the cryptocurrency market effectively.
''')

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Please try again later.")
