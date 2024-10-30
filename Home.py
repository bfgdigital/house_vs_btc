import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import statistics as stats
import numpy_financial as npf

from calcs import (
    calculate_lmi,
    home_investment_details,
    btc_investment_over_years,
    adjust_btc_for_inflation_and_cgt
)

# Set pandas display options for formatting
pd.options.display.float_format = '{:,.2f}'.format

# Define a consistent color palette
color_palette = {
    'Home Investment': '#1f77b4',  # Blue
    'BTC Investment': '#ff7f0e',   # Orange
    'Adjusted Equity': '#2ca02c',  # Green
    'Adjusted BTC Value': '#d62728',  # Red
    'Cumulative Investment': '#9467bd',  # Purple
    'Net Gain': '#8c564b',         # Brown
    'Rent Paid': '#e377c2',        # Pink
    'Interest': '#7f7f7f',         # Grey
    'Principal': '#bcbd22',        # Olive
    'House Price in BTC': '#17becf'  # Cyan
}

# Set up Streamlit page configuration
st.set_page_config(
    page_title='House vs. Bitcoin Investment Analysis',
    initial_sidebar_state='expanded',
)

pages = {
    "Home": "Home",
    "Housing Data": "Housing_Data",
    "Bitcoin Data": "Bitcoin_Data",
    "References": "References",
    "The Math": "The_Math",
}

# Streamlit app setup
st.title('Do You Really Need to Buy a House to "Get into the Market"?')

# Get current page from query params or default to home
current_page = st.query_params.get("page", "Home")

# Sidebar for user input
st.sidebar.header('Simulation Parameters')

st.sidebar.info("House Purchase Inputs")

# Input parameters
house_price: int = st.sidebar.number_input('House Price (AUD)', value=1000000, step=10000)
deposit: int = st.sidebar.number_input('Available Deposit (AUD)', value=200000, step=10000)
annual_interest_rate_input: float = st.sidebar.number_input('Mortgage Interest Rate (%)', value=5.5, step=0.1)
annual_interest_rate: float = annual_interest_rate_input / 100
mortgage_term_years: int = st.sidebar.slider('Mortgage Term (Years)', min_value=15, max_value=30, value=30)
annual_income: int = st.sidebar.number_input('Starting Annual Income (AUD)', value=150000, step=10000)
living_expenses: int = st.sidebar.number_input('Monthly Living Expenses (AUD)', value=4000, step=200)

st.sidebar.info("Economic Inputs")

annual_house_growth_rate_input: float = st.sidebar.number_input('Annual House Price Growth Rate (%)', value=6.0, step=0.1)
annual_house_growth_rate: float = annual_house_growth_rate_input / 100
annual_property_costs: int = st.sidebar.number_input('First Year Property Costs (AUD)', value=5000, step=500)
inflation_rate_input: float = st.sidebar.number_input('Inflation Rate (%)', value=3.5, step=0.1)
inflation_rate: float = inflation_rate_input / 100
cgt_rate_input: float = st.sidebar.number_input('Capital Gains Tax Rate (%)', value=20.0, step=1.0)
cgt_rate: float = cgt_rate_input / 100

st.sidebar.info("Bitcoin Inputs")
initial_btc_growth_rate_input: float = st.sidebar.number_input('Initial Bitcoin Annual Growth Rate (%)', value=25.0, step=1.0)
initial_btc_growth_rate: float = initial_btc_growth_rate_input / 100
final_btc_growth_rate_input: float = st.sidebar.number_input('Final Bitcoin Annual Growth Rate (%)', value=5.0, step=1.0)
final_btc_growth_rate: float = final_btc_growth_rate_input / 100
initial_btc_price: int = st.sidebar.number_input('Initial Bitcoin Price (AUD)', value=90000, step=1000)

st.sidebar.info("Time Period")
years_to_simulate: int = st.sidebar.slider('Simulation Period (Years)', min_value=5, max_value=30, value=15)

# Mortgage affordability and LMI calculation
loan_amount: int = house_price - deposit
lmi_cost: float = calculate_lmi(loan_amount, house_price)
loan_amount += lmi_cost  # Add LMI to loan amount
monthly_interest_rate: float = annual_interest_rate / 12
monthly_mortgage_payment = -npf.pmt(monthly_interest_rate, mortgage_term_years * 12, loan_amount)
weekly_mortgage_payment = monthly_mortgage_payment * 12 / 52
monthly_income: float = annual_income / 12
monthly_surplus: float = monthly_income - living_expenses - monthly_mortgage_payment

# Home investment details
(home_values, mortgage_balances, equities, annual_interest, annual_principal, 
 annual_costs_list, cumulative_investment_home, amortization_schedule) = home_investment_details(
    house_price, deposit, annual_house_growth_rate, annual_interest_rate, mortgage_term_years, years_to_simulate, annual_property_costs, inflation_rate)

monthly_interest: float = stats.mean(annual_interest) / 12
monthly_principal: float = stats.mean(annual_principal) / 12

weekly_interest: float = stats.mean(annual_interest) / 52
weekly_principal: float = stats.mean(annual_principal) / 52

# Calculate initial annual rent (equal to the first year's mortgage interest payment)
initial_annual_rent = annual_interest[0]

# Calculate annual rent paid, adjusted for inflation
annual_rent_paid = [
    initial_annual_rent * ((1 + inflation_rate) ** (year - 1))
    for year in range(1, years_to_simulate + 1)
]

# Cumulative rent paid over time
cumulative_rent = np.cumsum(annual_rent_paid)

# Calculate annual Bitcoin investment amounts (homeowner's principal payments + property costs)
btc_investment_per_year = [
    principal + costs
    for principal, costs in zip(annual_principal, annual_costs_list)
]

# BTC Investment Calculations
years_range: list = np.arange(1, years_to_simulate + 1)

# Generate decreasing BTC growth rates over the years
btc_growth_rates: list = np.linspace(initial_btc_growth_rate, final_btc_growth_rate, years_to_simulate)

total_bitcoins = 21_000_000  # Total number of bitcoins in circulation

(btc_values, total_invested_list, btc_holdings_list, cumulative_investment_btc, btc_prices) = btc_investment_over_years(
    deposit,
    initial_btc_price,
    btc_investment_per_year,
    btc_growth_rates,
    years_to_simulate
)

btc_adjusted_values: list = adjust_btc_for_inflation_and_cgt(
    btc_values,
    inflation_rate,
    cgt_rate,
    years_range,
    total_invested_list
)

# Ensure all lists have the same length as years_to_simulate
btc_values: list = btc_values[:years_to_simulate]
total_invested_list: list = total_invested_list[:years_to_simulate]
btc_adjusted_values: list = btc_adjusted_values[:years_to_simulate]
btc_holdings_list: list = btc_holdings_list[:years_to_simulate]
cumulative_rent: list = cumulative_rent[:years_to_simulate]
cumulative_investment_btc: list = cumulative_investment_btc[:years_to_simulate]
btc_prices: list = btc_prices[:years_to_simulate]

# Prepare DataFrames
btc_data: pd.DataFrame = pd.DataFrame({
    'Year': years_range,
    'BTC Investment Value (AUD)': btc_values,
    'Total Invested (AUD)': total_invested_list,
    'Inflation & Tax Adjusted BTC Value (AUD)': btc_adjusted_values,
    'BTC Holdings': btc_holdings_list,
    'Cumulative Rent Paid (AUD)': cumulative_rent,
    'Cumulative Investment (AUD)': cumulative_investment_btc,
    'BTC Price (AUD)': btc_prices,
    'Annual BTC Investment (AUD)': btc_investment_per_year,
    'Bitcoin Annual Growth Rate (%)': btc_growth_rates * 100
})

btc_data.set_index('Year', inplace=True)

# Home Equity Data
home_data: pd.DataFrame = pd.DataFrame({
    'Year': years_range,
    'Home Value (AUD)': home_values,
    'Mortgage Balance (AUD)': mortgage_balances,
    'Equity (AUD)': equities,
    'Inflation-Adjusted Equity (AUD)': [equity / ((1 + inflation_rate) ** (year - 1)) for equity, year in zip(equities, years_range)],
    'Cumulative Investment (AUD)': cumulative_investment_home,
    'Annual Interest (AUD)': annual_interest,
    'Annual Principal (AUD)': annual_principal,
    'Annual Property Costs (AUD)': annual_costs_list
})

home_data.set_index('Year', inplace=True)

# Calculate the Bitcoin market cap
final_btc_price: float = btc_prices[-1]
btc_market_cap: float = final_btc_price * total_bitcoins

house_price_in_btc: list = [house_value / btc_price for house_value, btc_price in zip(home_values, btc_prices)]

# Content

st.write("The 'Australian Dream' often revolves around owning a home. However, with real estate prices soaring, saving a deposit feels like chasing a moving target. Inflation doesn't help either—it increases living costs, making it harder to save.")
st.write("So, is buying a house the only path to long-term financial security?")

st.write("Suppose you're in the market for a house you can afford—not your dream home, but a start.")

financial_situation = {
    'House Price': f"${house_price:,.0f}",
    'Available Deposit': f"${deposit:,.0f}",
    'Loan Amount (including LMI)': f"${loan_amount:,.0f}",
    'Lenders Mortgage Insurance (LMI) Cost': f"${lmi_cost:,.0f}",
    'Annual Interest Rate on the Loan': f"{annual_interest_rate_input}%",
    'Weekly Mortgage Payment': f"${weekly_mortgage_payment:,.2f}",
    'Interest Component': f"${weekly_interest:,.2f}",
    'Principal Component': f"${weekly_principal:,.2f}",
    'Monthly Surplus After Expenses and Mortgage': f"${monthly_surplus:,.2f}",
}


st.table(financial_situation)

if monthly_surplus >= 0:
    st.success("You can likely afford the mortgage payments based on your current income and expenses.")
else:
    st.error("You cannot afford the mortgage payments based on your current income and expenses.")
    st.write("Consider adjusting the house price or increasing your deposit.")
    st.stop()

st.header("Projected Home Equity Growth Over Time")

st.write("""
The classic Aussie wealth generator. The family household. Our parents, the "Bank of Mum and Dad"'s biggest asset, is typically their house. They've been the rock of stability and symbol of prosperity.
         Buy a house and you're likely going to see the equity tied up in that house do the following.
         
""")

fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(years_range, home_data['Inflation-Adjusted Equity (AUD)'], label='Inflation-Adjusted Home Equity', marker='s', color=color_palette['Adjusted Equity'])
ax1.set_xlabel('Year')
ax1.set_ylabel('Adjusted Value (AUD)')
ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax1.set_title('Inflation-Adjusted Home Equity Over Time')
ax1.legend()
ax1.grid(True)
st.pyplot(fig1)

st.write("""
This traditional approach shows your wealth growing over time through home equity. Historically, property values have increased annually due to factors like location and land size.
""")

australian_housing_growth = {
    'NSW': 6.87,
    'VIC': 4.72,
    'QLD': 6.04,
    'SA': 5.96,
    'WA': 3.71,
    'TAS': 6.57,
    'NT': 1.17,
    'ACT': 4.45,
}

# Create DataFrame for housing growth
housing_growth_df = pd.DataFrame.from_dict(australian_housing_growth, orient='index', columns=['Average Annual Growth (%)'])
housing_growth_df.index.name = 'State/Territory'

# Apply heatmap styling
styled_housing_growth_df = housing_growth_df.style.background_gradient(cmap='RdYlGn', axis=0)

st.subheader("Australian Housing Growth Rates")
st.markdown("""
The table below shows the average annual growth rates for residential property prices across different Australian states and territories.
""")
st.dataframe(styled_housing_growth_df)

# Display Home Data Table
st.subheader("Detailed Home Investment Data")

with st.expander("View Home Investment Details"):
    # Apply heatmap to 'Inflation-Adjusted Equity (AUD)'
    styled_home_data = home_data.style.background_gradient(cmap='RdYlGn', subset=['Inflation-Adjusted Equity (AUD)'])
    st.dataframe(styled_home_data)

st.divider()

# Additional Chart: Breakdown of Mortgage Payments Over Time
st.subheader('Breakdown of Mortgage Payments Over Time')

st.write("""
So what's involved in owning a house, typically a loan from the bank, which you pay back over time.
The amount you pay back each week, fortnight, month etc, is typically made up of 2 or 3 factors:
- Principal: Giving back the original amount of money the bank gave you.
- Interest: A fee/payment to the bank on top of the money you borrowed for the money they've lent you.
- Fees: Some administrative fees which are usually pretty small, in the realm of $500 for extra features like offset accounts.
""")

st.write("""
To keep it simple, I'll ignore administrative fees.
""")

st.write("""
Understanding how your mortgage payments are allocated between interest and principal over time can provide insights into how much of your money is building equity versus paying interest to the bank/lender.
""")

interest_mean = sum(annual_interest[:years_to_simulate]) / len(annual_interest[:years_to_simulate])

fig_payment, ax_payment = plt.subplots(figsize=(10, 6))
ax_payment.stackplot(years_range, annual_interest[:years_to_simulate], annual_principal[:years_to_simulate], labels=['Interest', 'Principal'], colors=[color_palette['Interest'], color_palette['Principal']])
ax_payment.axhline(y=interest_mean, color='r', linestyle='--', label='Interest Mean')
ax_payment.set_xlabel('Year')
ax_payment.set_ylabel('Amount (AUD)')
ax_payment.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_payment.set_title('Annual Mortgage Payment Breakdown')
ax_payment.legend()
ax_payment.grid(True)
st.pyplot(fig_payment)

st.write(f"""
On average over the timeframe, approximately **${interest_mean:,.0f}** is paid to the bank each year as interest. This amount is a pure expense, similar to paying rent.
""")

# Display Mortgage Amortization Schedule
st.subheader("Mortgage Amortization Schedule")

with st.expander("View Amortization Schedule"):
    annual_amortization = amortization_schedule.groupby('Year').agg({
        'Interest': 'sum',
        'Principal': 'sum',
        'Balance': 'last'
    }).reset_index()
    st.dataframe(annual_amortization[['Year', 'Interest', 'Principal', 'Balance']].style.format('${:,.2f}'))

st.divider()

# Alternative Strategy: Investing in Bitcoin
st.header('So here\'s an alternative to buying a house as a wealth generator.')
st.info('Invest in Bitcoin')

st.write("""
Given the challenges of affording a home, let's look into the numbers for investing in Bitcoin as an alternative. 
Instead of using your deposit to buy a house, you invest it in Bitcoin upfront.
I wanted to make this as much of an Apples to Apples comparison as I could.
""")

st.write("""
This has proven hard and it's going to be controversial no matter what values I use.
So here is the strategy I've gone with:
- The funds that would have gone towards the principal portion of your mortgage payment and homeowner expenses are also invested in Bitcoin annually. 
- You use the equivalent of the interest portion of your mortgage payment to pay rent instead, adjusted each year for inflation.
""")

st.write(f"""
**Here's how it breaks down based on your inputs:**

- **Initial Investment in Bitcoin:** Your house deposit of \${deposit:,.0f}
- **Annual Bitcoin Investment:** The sum of your annual principal payments and homeowner expenses, which starts at approximately \${int(btc_investment_per_year[0]):,.0f} in the first year.
""")

st.write(f"""
Then you still have rent to pay, and the budget for that is based on how much you would have paid in interest on your mortgage.
This can vary depending on where you want to live, but works well as a rule of thumb for being able to rent where you wanted to buy.
- **Annual Rent Payment:** Equivalent to your annual mortgage interest payments, adjusted for inflation, starting at approximately \${int(annual_rent_paid[0]):,.0f} in the first year.
""")

st.divider()

st.subheader('Elephant in the room. How much will Bitcoin\'s value rise?')

st.write("""
Bitcoin has had a volatile but upward-trending history. While past performance doesn't guarantee future results, let's use a decreasing growth rate to simulate a more realistic future scenario.
For argument's sake, I want to completely divorce Bitcoin from any other form of 'crypto', and the reasons for that can be
heard and argued in language far better than I can deliver in "Broken Money" by Lyn Alden or "The Bitcoin Standard" by Saifedean Ammous.
""")

st.write(f"""
I don't think the past growth rates can continue as Bitcoin adoption matures and it becomes more common, so I've gone with a super simple growth model.
Pick a reasonable growth rate for today ({initial_btc_growth_rate_input}%) and a reasonable final growth rate in the future when it's matured much more ({final_btc_growth_rate_input}%).
""")

st.write(f"""
With the values selected we have a final Market Cap value of \${btc_market_cap/1e12:,.2f} Trillion AUD. 

For reference, the Market Cap of Gold is around \$28.57 Trillion AUD, the whole of the Australian Residential Property Market is around \$11 Trillion AUD, currently BTC Market Cap is around \$2.18 Trillion AUD.
So, if this doesn't feel right, adjust it. 

So many people have tried to figure this out and estimated it. It's a crucial input that makes or breaks the outcome,
so I suggest doing some homework and seeing what you can come up with. 

I've gone with a pretty flexible assumption that all 21 million BTC are already available to use (they're not), with none of them being lost (which they have),
so I'm putting some padding in there for argument's sake. 
""")

st.write("""
As you can see, the Bitcoin growth rate starts at your initial rate and decreases to your final rate by the end of the simulation period.
""")

st.write("""
Let's see how this alternative strategy could play out over the same time period.
""")

# Show BTC growth rates over time
st.subheader("Bitcoin Growth Rates Over Time")

with st.expander("View BTC Growth Rates and Investment Details"):
    st.dataframe(btc_data[['Bitcoin Annual Growth Rate (%)', 'BTC Price (AUD)', 'Annual BTC Investment (AUD)']].style.format({'Bitcoin Annual Growth Rate (%)': '{:.2f}%', 'BTC Price (AUD)': '${:,.2f}', 'Annual BTC Investment (AUD)': '${:,.2f}'}))

# Plotting the BTC Investment vs. Rent
st.subheader('Raw Bitcoin Investment Value vs. Cumulative Rent Paid')

st.write(f"""
So, instead of a mortgage, you rent. You spend the amount you're paying on your mortgage interest on rent,
and the amount you're spending on principal (the money you would be 'saving') plus homeowner expenses on Bitcoin. Both rent and expenses are adjusted for inflation.

Based on the inputs you've provided, that would be:
- **First Year Rent:** Approximately \${int(annual_rent_paid[0]):,.0f} per year
- **First Year Bitcoin Investment:** Approximately \${int(btc_investment_per_year[0]):,.0f} per year

So how does this look over the same time period with a decreasing Bitcoin growth rate?
""")

fig2, ax2 = plt.subplots(figsize=(10, 6))
ax2.plot(years_range, btc_values, label='Bitcoin Investment Value', marker='o', color=color_palette['BTC Investment'])
ax2.plot(years_range, cumulative_rent, label='Cumulative Rent Paid', marker='s', color=color_palette['Rent Paid'])
ax2.set_xlabel('Year')
ax2.set_ylabel('Amount (AUD)')
ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax2.set_title('Bitcoin Investment vs. Rent Over Time')
ax2.legend()
ax2.grid(True)
st.pyplot(fig2)

st.write("""
So even while paying rent, using a decreasing Bitcoin annual growth rate, we're looking at a significant increase in
equity. But of course, it's not that simple.
""")

# Display Bitcoin Investment Data Table
st.subheader("Detailed Bitcoin Investment Data")

with st.expander("View Bitcoin Investment Details"):
    styled_btc_data = btc_data.style.background_gradient(cmap='RdYlGn', subset=['Inflation & Tax Adjusted BTC Value (AUD)'])
    st.dataframe(styled_btc_data.format({'Inflation & Tax Adjusted BTC Value (AUD)': '${:,.2f}'}))

# Additional Chart: Cumulative Investment vs. Adjusted Equity/Value Over Time
st.subheader('Cumulative Investment vs. Adjusted Equity/Value Over Time')

st.write("""
Comparing how much you've invested over time against the adjusted equity or value of your investments can help you understand the efficiency and effectiveness of each strategy.
""")

fig_cumulative, ax_cumulative = plt.subplots(figsize=(10, 6))
ax_cumulative.plot(years_range, home_data['Cumulative Investment (AUD)'], label='Cumulative Home Investment', linestyle='--', color=color_palette['Cumulative Investment'])
ax_cumulative.plot(years_range, home_data['Inflation-Adjusted Equity (AUD)'], label='Inflation-Adjusted Home Equity', marker='s', color=color_palette['Adjusted Equity'])
ax_cumulative.plot(years_range, btc_data['Cumulative Investment (AUD)'], label='Cumulative BTC Investment', linestyle='--', color=color_palette['Cumulative Investment'])
ax_cumulative.plot(years_range, btc_data['Inflation & Tax Adjusted BTC Value (AUD)'], label='Inflation & Tax Adjusted BTC Value', marker='o', color=color_palette['Adjusted BTC Value'])
ax_cumulative.set_xlabel('Year')
ax_cumulative.set_ylabel('Amount (AUD)')
ax_cumulative.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_cumulative.set_title('Cumulative Investment vs. Adjusted Equity/Value Over Time')
ax_cumulative.legend()
ax_cumulative.grid(True)
st.pyplot(fig_cumulative)

st.write("""
This chart shows how your investments grow over time compared to how much you've actually put in. It highlights the power of compounding returns and the impact of different growth rates.
""")

# Additional Chart: Net Gain Over Time
st.subheader('Net Gain Over Time')

st.write("""
Net gain represents the adjusted equity or value minus the cumulative investment. It effectively shows your profit after accounting for all the money you've invested.
""")

home_net_gain = home_data['Inflation-Adjusted Equity (AUD)'] - home_data['Cumulative Investment (AUD)']
btc_net_gain = btc_data['Inflation & Tax Adjusted BTC Value (AUD)'] - btc_data['Cumulative Investment (AUD)']

fig_net_gain, ax_net_gain = plt.subplots(figsize=(10, 6))
ax_net_gain.plot(years_range, home_net_gain, label='Home Net Gain', marker='s', color=color_palette['Adjusted Equity'])
ax_net_gain.plot(years_range, btc_net_gain, label='BTC Net Gain', marker='o', color=color_palette['Adjusted BTC Value'])
ax_net_gain.set_xlabel('Year')
ax_net_gain.set_ylabel('Net Gain (AUD)')
ax_net_gain.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_net_gain.set_title('Net Gain Over Time')
ax_net_gain.legend()
ax_net_gain.grid(True)
st.pyplot(fig_net_gain)

st.write("""
This chart illustrates the actual profit you've made from each investment after accounting for all your contributions. It provides a clear picture of which investment is yielding higher returns over time.
""")

# Additional Chart: Total Costs of Owning a Home vs. Renting
st.subheader('Total Costs: Owning a Home vs. Renting')

st.write("""
Comparing the total costs associated with owning a home (interest payments and property costs) to renting can help you understand the financial commitments of each option.
""")

total_home_costs = [interest + cost for interest, cost in zip(annual_interest, annual_costs_list)]
cumulative_home_costs = np.cumsum(total_home_costs)
cumulative_rent_costs = cumulative_rent

fig_total_costs, ax_total_costs = plt.subplots(figsize=(10, 6))
ax_total_costs.plot(years_range, cumulative_home_costs, label='Cumulative Home Costs', marker='s', color=color_palette['Home Investment'])
ax_total_costs.plot(years_range, cumulative_rent_costs, label='Cumulative Rent Costs', marker='o', color=color_palette['Rent Paid'])
ax_total_costs.set_xlabel('Year')
ax_total_costs.set_ylabel('Total Costs (AUD)')
ax_total_costs.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_total_costs.set_title('Total Costs of Owning a Home vs. Renting')
ax_total_costs.legend()
ax_total_costs.grid(True)
st.pyplot(fig_total_costs)

st.write("""
This chart helps you see how much money is going out over time in each scenario. While owning a home involves significant costs, some of these payments build equity, whereas rent is purely an expense.
""")

# Effect of Inflation and CGT on Bitcoin Investment
st.subheader('Effect of Capital Gains Tax on Bitcoin Investment')

st.write("""
Understanding how capital gains tax (CGT) impacts your Bitcoin investment is crucial. This chart shows the raw Bitcoin investment value and the value after capital gains tax.

It's important to remember that you only pay the CGT if you sell. If you decide to not sell and continue investing, your wealth may continue to grow.
""")

btc_value_after_cgt = [
    btc_value - ((btc_value - invested) * cgt_rate) if btc_value > invested else btc_value
    for btc_value, invested in zip(btc_values, total_invested_list)
]

fig_cgt, ax_cgt = plt.subplots(figsize=(10, 6))
ax_cgt.plot(years_range, btc_values, label='Raw BTC Value', linestyle='--', color=color_palette['BTC Investment'])
ax_cgt.plot(years_range, btc_value_after_cgt, label='After CGT', marker='o', color=color_palette['Adjusted BTC Value'])
ax_cgt.set_xlabel('Year')
ax_cgt.set_ylabel('Value (AUD)')
ax_cgt.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_cgt.set_title('Effect of Capital Gains Tax on Bitcoin Investment')
ax_cgt.legend()
ax_cgt.grid(True)
st.pyplot(fig_cgt)

st.write("""
This chart highlights the importance of considering taxes when evaluating investment returns. While the raw Bitcoin value might look impressive, the actual amount after taxes is what you would receive if you sold your investment.
""")

# Adjusting for Inflation and Purchasing Power
st.subheader('Purchasing Power and Inflation')

st.write("""
Inflation reduces the purchasing power of money over time, affecting both cash and investments. To understand the real value of your investments, it's important to adjust for inflation.

In this section, we'll compare the purchasing power of both the home equity and the Bitcoin investment by adjusting for inflation.
""")

# Adjust home equity and BTC investment for inflation
inflation_adjusted_home_equity = [
    equity / ((1 + inflation_rate) ** (year - 1))
    for equity, year in zip(home_data['Equity (AUD)'], years_range)
]

inflation_adjusted_btc_value = [
    value / ((1 + inflation_rate) ** (year - 1))
    for value, year in zip(btc_values, years_range)
]

fig_inflation, ax_inflation = plt.subplots(figsize=(10, 6))
ax_inflation.plot(
    years_range,
    inflation_adjusted_home_equity,
    label='Inflation-Adjusted Home Equity',
    marker='s',
    color=color_palette['Adjusted Equity']
)
ax_inflation.plot(
    years_range,
    inflation_adjusted_btc_value,
    label='Inflation-Adjusted BTC Value',
    marker='o',
    color=color_palette['Adjusted BTC Value']
)
ax_inflation.plot(years_range, home_data['Equity (AUD)'], label='Home Net Gain', linestyle='--', marker='s', color=color_palette['Adjusted Equity'])
ax_inflation.plot(years_range, btc_values, label='BTC Net Gain', linestyle='--', marker='o', color=color_palette['Adjusted BTC Value'])
ax_inflation.set_xlabel('Year')
ax_inflation.set_ylabel('Value (AUD in today\'s dollars)')
ax_inflation.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_inflation.set_title('Purchasing Power of Investments Over Time (Adjusted for Inflation)')
ax_inflation.legend()
ax_inflation.grid(True)
st.pyplot(fig_inflation)

st.write("""
This chart shows the purchasing power of your investments over time, adjusted for inflation. By adjusting both investments for inflation, we can see how their real value compares in today's dollars.
""")

# House Price in Bitcoin
st.subheader('House Price in Bitcoin Over Time')

fig4, ax4 = plt.subplots(figsize=(10, 6))
ax4.plot(years_range, house_price_in_btc, label='House Price in Bitcoin', marker='^', color=color_palette['House Price in BTC'])
ax4.set_xlabel('Year')
ax4.set_ylabel('House Price (BTC)')
ax4.set_title('House Price in Bitcoin Over Time')
ax4.legend()
ax4.grid(True)
st.pyplot(fig4)

st.write("""
This chart shows how many Bitcoins would be required to purchase the house over time. If Bitcoin appreciates faster than the house price, the number of Bitcoins needed decreases, enhancing your purchasing power relative to the housing market.
""")

# Conclusion
st.header('Conclusion')

final_btc_value = btc_adjusted_values[-1]
final_home_equity = home_data['Inflation-Adjusted Equity (AUD)'].iloc[-1]

if final_btc_value > final_home_equity:
    st.write(f"By investing in Bitcoin, you could potentially have **\${final_btc_value:,.0f}** in adjusted value after {years_to_simulate} years, compared to **\${final_home_equity:,.0f}** in home equity.")
    st.write("Investing in Bitcoin might be a viable alternative to purchasing a home, especially if housing affordability is a concern in the short term. You can start buying Bitcoin today and transfer it into a house when it better suits your needs.")
else:
    st.write(f"By purchasing a home, you could potentially have **\${final_home_equity:,.0f}** in adjusted equity after {years_to_simulate} years, compared to **\${final_btc_value:,.0f}** from investing in Bitcoin.")
    st.write("Purchasing a home could be a better investment over the long term.")

st.write("""
**Note:** This analysis is based on projections and assumptions that may not hold true in reality. Investment decisions should be made after consulting with a qualified financial advisor that understands Bitcoin properly.

While Bitcoin has shown incredible growth in the past, it is also known for its volatility. Long-term growth trends have been positive, but past performance is not indicative of future results.
""")

st.write("""
Feel free to adjust the parameters in the sidebar to see how different values affect the outcome. Experimenting with various scenarios can help you better understand the potential risks and rewards associated with each investment strategy.
""")

st.write("""
If you're interested in how I came up with these numbers, you can check out the math in the `calcs.py` file.
         
Cheers and keep your head up Australia!
""")
