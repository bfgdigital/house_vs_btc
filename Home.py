# House.py

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import statistics as stats
import numpy_financial as npf

from calcs.housing_calcs import (
    simulate_house_purchase_and_investment,
)

from calcs.btc_calcs import (
    simulate_and_adjust_btc_investment,
    generate_btc_growth_rates
)

# Set pandas display options for formatting
pd.options.display.float_format = '{:,.2f}'.format

############################################################
# Streamlit Configuration

# Define a consistent colour palette
color_palette = {
    'House Investment': '#1f77b4',
    'BTC Investment': '#ff7f0e',
    'Adjusted Equity': '#2ca02c',
    'Adjusted BTC Value': '#d62728',
    'Cumulative Investment': '#9467bd',
    'Net Gain': '#8c564b',
    'Rent Paid': '#e377c2',
    'Interest': '#7f7f7f',
    'Principal': '#bcbd22',
    'House Price in BTC': '#17becf'
}

# Streamlit page configuration
st.set_page_config(
    page_title='House vs. Bitcoin Investment Analysis',
    initial_sidebar_state='expanded',
)

# Define navigation pages (if applicable)
pages = {
    "House": "House",
    "Housing Data": "Housing_Data",
    "Inflation Data": "Inflation_Data",
    "Bitcoin Data": "Bitcoin_Data",
    "References": "References",
    "The Math": "The_Math",
}

# Get current page from query params or default to house
current_page = st.query_params.get("page", ["House"])[0]

############################################################
# Streamlit Sidebar

# Sidebar for user input
st.sidebar.header('Simulation Parameters')

st.sidebar.text("I don't want to argue with anyone about numbers, so you can use your own. I've set some defaults, but you can change them.")
st.sidebar.info("House Purchase Inputs")

# Input parameters
house_price: int = st.sidebar.number_input('House Price (AUD)', value=1_000_000, step=10_000)
deposit: int = st.sidebar.number_input('Available Deposit (AUD)', value=200_000, step=10_000)
annual_interest_rate_input: float = st.sidebar.number_input('Mortgage Interest Rate (%)', value=5.5, step=0.1)
annual_interest_rate: float = annual_interest_rate_input / 100
mortgage_term_years: int = st.sidebar.slider('Mortgage Term (Years)', min_value=15, max_value=30, value=30)
annual_income: int = st.sidebar.number_input('Starting Annual Income (AUD)', value=150_000, step=10_000)

st.sidebar.info("Economic Inputs")

annual_house_growth_rate_input: float = st.sidebar.number_input('Annual House Price Growth Rate (%)', value=6.0, step=0.1)
annual_house_growth_rate: float = annual_house_growth_rate_input / 100
annual_property_costs: int = st.sidebar.number_input('First Year Property Costs (AUD)', value=5_000, step=500)
inflation_rate_input: float = st.sidebar.number_input('Inflation Rate (%)', value=3.5, step=0.1)
inflation_rate: float = inflation_rate_input / 100
cgt_rate_input: float = st.sidebar.number_input('Capital Gains Tax Rate (%)', value=20.0, step=1.0)
cgt_rate: float = cgt_rate_input / 100

st.sidebar.info("Bitcoin Inputs")
initial_btc_growth_rate_input: float = st.sidebar.number_input('Initial Bitcoin Annual Growth Rate (%)', value=25.0, step=1.0)
initial_btc_growth_rate: float = initial_btc_growth_rate_input / 100
final_btc_growth_rate_input: float = st.sidebar.number_input('Final Bitcoin Annual Growth Rate (%)', value=5.0, step=1.0)
final_btc_growth_rate: float = final_btc_growth_rate_input / 100
initial_btc_price: int = st.sidebar.number_input('Initial Bitcoin Price (AUD)', value=90_000, step=1_000)

st.sidebar.info("Time Period")
years_to_simulate: int = st.sidebar.slider('Simulation Period (Years)', min_value=5, max_value=30, value=15)

############################################################
# Simulation Calculations

# Simulate House Purchase and Investment
house_simulation = simulate_house_purchase_and_investment(
    house_price=house_price,
    deposit=deposit,
    annual_house_growth_rate=annual_house_growth_rate,
    mortgage_interest_rate=annual_interest_rate,
    mortgage_term_years=mortgage_term_years,
    years_to_simulate=years_to_simulate,
    annual_property_costs=annual_property_costs,
    inflation_rate=inflation_rate,
    annual_income=annual_income
)

# Extract Mortgage Details
mortgage_details = house_simulation['mortgage_details']
loan_amount: float = mortgage_details.loan_amount
lmi_cost: float = mortgage_details.lmi_cost
monthly_mortgage_payment: float = mortgage_details.monthly_mortgage_payment
weekly_mortgage_payment: float = mortgage_details.weekly_mortgage_payment
monthly_income: float = mortgage_details.monthly_income
monthly_surplus: float = mortgage_details.monthly_surplus

# Extract House Investment Details
house_investment = house_simulation['house_investment_details']
house_values = house_investment.house_values
mortgage_balances = house_investment.mortgage_balances
equities = house_investment.equities
annual_interest = house_investment.annual_interest
annual_principal = house_investment.annual_principal
annual_costs_list = house_investment.annual_property_costs
cumulative_investment_house = house_investment.cumulative_investment_house
amortization_schedule = house_investment.amortization_schedule.schedule_df

# Calculate mean annual interest and principal for display
monthly_interest: float = stats.mean(annual_interest) / 12
monthly_principal: float = stats.mean(annual_principal) / 12
weekly_interest: float = stats.mean(annual_interest) / 52
weekly_principal: float = stats.mean(annual_principal) / 52

# Calculate annual rent paid
rent_details = house_simulation['rent_details']
initial_annual_rent = rent_details.initial_annual_rent
annual_rent_paid = rent_details.annual_rent_paid
cumulative_rent = rent_details.cumulative_rent_paid

# Simulate Bitcoin Investment
btc_simulation = simulate_and_adjust_btc_investment(
    initial_investment=deposit,
    initial_btc_price=initial_btc_price,
    annual_investment_amounts=[
        principal + cost for principal, cost in zip(annual_principal, annual_costs_list)
    ],
    initial_growth_rate=initial_btc_growth_rate,
    final_growth_rate=final_btc_growth_rate,
    years=years_to_simulate,
    cgt_rate=cgt_rate,
    inflation_rate=inflation_rate
)

# Extract BTC Simulation Results
btc_sim_result = btc_simulation['simulation_result']
btc_after_tax_values = btc_simulation['after_tax_values']
btc_purchasing_power_values = btc_simulation['purchasing_power']

# Extract BTC Investment Data
btc_values = btc_sim_result.btc_values
total_invested_list = btc_sim_result.total_invested
btc_holdings_list = btc_sim_result.btc_holdings
cumulative_investment_btc = btc_sim_result.cumulative_invested
btc_prices = btc_sim_result.btc_prices
annual_btc_investment = btc_sim_result.annual_invested
years_simulated = btc_sim_result.years  # Access 'years'

# Calculate Bitcoin Market Cap
total_bitcoins = 21_000_000  # Total number of bitcoins in circulation
final_btc_price: float = btc_prices[-1]
btc_market_cap: float = final_btc_price * total_bitcoins

# Calculate House Price in BTC
house_price_in_btc: list = [house_value / btc_price for house_value, btc_price in zip(house_values, btc_prices)]

# Create DataFrame with BTC Data
btc_data = pd.DataFrame({
    'Year': list(range(1, years_simulated + 1)),
    'BTC Investment Value (AUD)': btc_values,
    'Total Invested (AUD)': total_invested_list,
    'After Tax BTC Value (AUD)': btc_after_tax_values,
    'Inflation & Tax Adjusted BTC Value (AUD)': btc_purchasing_power_values,
    'BTC Holdings': btc_holdings_list,
    'Cumulative Investment (AUD)': cumulative_investment_btc,
    'BTC Price (AUD)': btc_prices,
    'Annual BTC Investment (AUD)': annual_btc_investment,
    'Bitcoin Annual Growth Rate (%)': [
        rate * 100 for rate in generate_btc_growth_rates(initial_btc_growth_rate, final_btc_growth_rate, years_simulated)
    ]
})

btc_data.set_index('Year', inplace=True)

############################################################
# House Investment Variables and Calculations

years_range: list = list(range(1, years_simulated + 1))

inflation_adjusted_house_equity = [
    equity / ((1 + inflation_rate) ** (year - 1)) 
    for equity, year in zip(equities, years_range)
]

house_data = pd.DataFrame({
    'Year': years_range,
    'House Value (AUD)': house_values,
    'Mortgage Balance (AUD)': mortgage_balances,
    'Equity (AUD)': equities,
    'Cumulative Investment (AUD)': cumulative_investment_house,
    'Annual Interest (AUD)': annual_interest,
    'Annual Principal (AUD)': annual_principal,
    'Annual Property Costs (AUD)': annual_costs_list,
    'Inflation-Adjusted Equity (AUD)': inflation_adjusted_house_equity
})

house_data.set_index('Year', inplace=True)

############################################################
# Streamlit Content

# Streamlit app setup
st.title('Do You Really Need to Buy a House and "Get into the Market"?')

st.write("The 'Australian Dream' often revolves around owning a house. However, with real estate prices soaring, and an increasing cost of living, saving a deposit feels like chasing a moving target.")
st.write("So, somehow, buying a house has become the Aussie escape pod, the only path to long-term financial security.")
st.write("This hasn't sat well with me for some time, so I've decided to put some numbers on the table to see if there are any other options.")

st.write("Suppose you're in the market for a house you can afford. Not your dream house, but a start.")

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
    st.success("Great, You can likely afford the mortgage payments based on your current income and expenses.")
else:
    st.error("It's unlikely you can afford the mortgage payments based on your current income and expenses.")
    st.write("We've built this tool on affording mortgage payments, so don't worry if you're not there yet, this might end up getting you there.")
    st.write("In the meantime, adjust either the house price or increase your deposit.")
    st.stop()

st.header("Projected House Equity Growth Over Time")

st.write("""
The classic Aussie wealth generator. The family household. Our parents wealth typically comes from their house. The family house has been the rock of stability and symbol of prosperity.
What does that mean? Well if you buy a house and you're likely going to see the equity tied up in that house do the following.
""")

# Update the visualization for raw equity
fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(years_range, house_data['Equity (AUD)'], label='House Equity', marker='s', color=color_palette['House Investment'])
ax1.set_xlabel('Year')
ax1.set_ylabel('Value (AUD)')
ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax1.set_title('House Equity Over Time')
ax1.legend()
ax1.grid(True)
st.pyplot(fig1)

st.write("""
Looks good hey? This traditional approach to building wealth shows your wealth growing over time through house equity. 
""")

# Display House Data Table
st.subheader("Here's the breakdown of your house investment over time")

with st.expander("View House Investment Details"):
    # Apply heatmap to 'Inflation-Adjusted Equity (AUD)'
    styled_house_data = house_data.style.background_gradient(cmap='bwr', subset=['Inflation-Adjusted Equity (AUD)'])
    st.dataframe(styled_house_data)

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

# Create DataFrame for housing growth, sorted by growth rate
housing_growth_df = pd.DataFrame.from_dict(australian_housing_growth, orient='index', columns=['Average Annual Growth (%)'])
housing_growth_df.index.name = 'State/Territory'
housing_growth_df = housing_growth_df.sort_values(by='Average Annual Growth (%)', ascending=False)

# Apply heatmap styling
styled_housing_growth_df = housing_growth_df.style.background_gradient(cmap='bwr', axis=0)

st.subheader("Australian Housing Growth Rates")
st.markdown("""
The table below shows the average annual growth rates for residential property prices across different Australian states and territories.
The housing market data is sourced from the Australian Bureau of Statistics (ABS), specifically from [ABS Total Value of Dwellings Report](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings). This dataset contains historical mean price data of residential dwellings across Australian states and territories, reported quarterly.
If you want to check it out, you can download it from that link or use the file I'm using in the tool here: [Xlxs File](https://github.com/bfgdigital/house_vs_btc/blob/main/data/643201.xlsx)
""")
st.dataframe(styled_housing_growth_df)

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

interest_mean = sum(annual_interest[:years_simulated]) / len(annual_interest[:years_simulated])

fig_payment, ax_payment = plt.subplots(figsize=(10, 6))
ax_payment.stackplot(
    years_range,
    annual_interest[:years_simulated],
    annual_principal[:years_simulated],
    labels=['Interest Paid', 'Principal Paid'],
    colors=[color_palette['Interest'], color_palette['Principal']]
)
ax_payment.axhline(y=interest_mean, color='r', linestyle='--', label='Interest Mean')
ax_payment.set_xlabel('Year')
ax_payment.set_ylabel('Amount (AUD)')
ax_payment.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_payment.set_title('Annual Mortgage Payment Breakdown')
ax_payment.legend()
ax_payment.grid(True)
st.pyplot(fig_payment)

st.write(f"""
On average over the timeframe, approximately **${interest_mean:,.0f}** is paid to the bank each *year* as interest. This amount is a pure expense, similar to paying rent.
""")

# Display Mortgage Amortization Schedule
st.subheader("Mortgage Amortization Schedule")

with st.expander("View Amortization Schedule"):
    annual_amortization = (
        amortization_schedule.groupby('Year')
        .agg({
            'Interest': 'sum',
            'Principal': 'sum',
            'Balance': 'last'
        })
        .reset_index()
    )

    # apply formatting and gradient to the DataFrame before passing to st.dataframe
    styled_df = (
        annual_amortization[['Year', 'Interest', 'Principal', 'Balance']]
        .style.format('${:,.2f}')
        .background_gradient(cmap='bwr', subset=['Balance'])
    )

    st.dataframe(styled_df)

st.divider()

# Alternative Strategy: Investing in Bitcoin
st.header('So here\'s an alternative to buying a house as a wealth generator.')
st.info('Invest in Bitcoin')

st.write("""
Given the challenges of affording a house, let's look into the numbers for investing in Bitcoin as an alternative. 
Instead of using your deposit to buy a house, you invest it in Bitcoin upfront.
I wanted to make this as much of an Apples to Apples comparison as I could.
""")

st.write("""
This has proven hard and it's going to be controversial no matter what values I use.
So here is the strategy I've gone with:
- The funds that would have gone towards the principal portion of your mortgage payment and houseowner expenses are also invested in Bitcoin annually. 
- You use the equivalent of the interest portion of your mortgage payment to pay rent instead, adjusted up each year, for inflation.
""")

st.write(f"""
**Here's how it breaks down based on your inputs:**

- **Initial Investment in Bitcoin:** Your house deposit of \${deposit:,.0f}
- **Annual Bitcoin Investment:** The sum of your annual principal payments and houseowner expenses, which starts at approximately \${int(annual_btc_investment[0]):,.0f} in the first year.
""")

st.write(f"""
Then you still have rent to pay, and the budget for that is based on how much you would have paid in interest on your mortgage.
This can vary depending on where you want to live, but works well as a rule of thumb for being able to rent where you intended to buy.
- **Annual Rent Payment:** Equivalent to your annual mortgage interest payments, adjusted for inflation, starting at approximately \${int(annual_rent_paid[0]):,.0f} in the first year.
""")

st.divider()

st.subheader('Elephant in the room. How much will Bitcoin\'s value rise?')

st.write("""
Bitcoin has had a fluctuating but generally upward-trending history. While past performance doesn't guarantee future results, let's use a decreasing growth rate to simulate a more realistic future scenario.
For argument's sake, I want to completely divorce Bitcoin from any other form of 'crypto', and the reasons for that can be
heard and argued in language far better than I can deliver in "Broken Money" by Lyn Alden or "The Bitcoin Standard" by Saifedean Ammous.
""")

st.write(f"""
I don't think the past growth rates can continue as Bitcoin adoption matures and it becomes more common, so I've gone with a super simple growth model.
Pick a reasonable growth rate for today ({initial_btc_growth_rate_input}%) and a reasonable final growth rate in the future when it's matured much more ({final_btc_growth_rate_input}%).
""")

st.write(f"""
At the time of writing, the price of bitcoin has risen 104% in the last 12 months. The historical, quarterly Bitcoin growth rate is just over 25%.
To keep things conservative,  I've used the historical quarterly Bitcoin growth rate as the starting point for my annual growth rate.
So just 1/4 of what it has been for the past 14 years.
""")

st.write(f"""
With the values selected we have a final Market Cap value of \${btc_market_cap/1e12:,.2f} Trillion AUD. 

For reference, the Market Cap of Gold is around \$30 Trillion AUD, the whole of the Australian Residential Property Market is around \$11 Trillion AUD, currently BTC Market Cap is around \$3 Trillion AUD.
So, if this doesn't feel right, adjust it. 

So many people have tried to figure this out and estimated it. It's a crucial input that makes or breaks the outcome,
so I suggest doing some housework and seeing what you can come up with. 

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
    # select relevant columns and apply styling
    styled_btc_data = (
        btc_data[
            [
                'Bitcoin Annual Growth Rate (%)',
                'BTC Price (AUD)',
                'Annual BTC Investment (AUD)',
                'BTC Investment Value (AUD)'
            ]
        ]
        .style.format(
            {
                'Bitcoin Annual Growth Rate (%)': '{:.2f}%',
                'BTC Price (AUD)': '${:,.2f}',
                'Annual BTC Investment (AUD)': '${:,.2f}',
                'BTC Investment Value (AUD)': '${:,.2f}'
            }
        )
        .background_gradient(cmap='bwr', subset=['Bitcoin Annual Growth Rate (%)'])  # highlight growth rate
        .background_gradient(cmap='bwr', subset=['BTC Investment Value (AUD)'])    # highlight investment value
    )

    st.dataframe(styled_btc_data)

# Plotting the BTC Investment vs. Rent
st.subheader('Raw Bitcoin Investment Value vs. Cumulative Rent Paid')

st.write(f"""
So, instead of a mortgage, you rent. You spend the amount you're paying on your mortgage interest on rent,
and the amount you're spending on principal (the money you would be 'saving') plus houseowner expenses on Bitcoin. Both rent and expenses are adjusted for inflation.

Based on the inputs you've provided, that would be:
- **First Year Rent:** Approximately \${int(annual_rent_paid[0]):,.0f} per year
- **First Year Bitcoin Investment:** Approximately \${int(annual_btc_investment[0]):,.0f} per year

So how does this pan out side by side over time?
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
    styled_btc_data = btc_data.style.background_gradient(cmap='bwr', subset=['Inflation & Tax Adjusted BTC Value (AUD)'])
    st.dataframe(styled_btc_data.format({'Inflation & Tax Adjusted BTC Value (AUD)': '${:,.2f}'}))

# Additional Chart: Cumulative Investment vs. Adjusted Equity/Value Over Time
st.subheader('Cumulative Investment vs. Adjusted Equity/Value Over Time')

st.write("""
Comparing how much you've invested over time against the adjusted equity or value of your investments can help you understand the efficiency and effectiveness of each strategy.
""")

# Plot 1: Cumulative Investment vs. Equity/Value (Raw Values)
fig_cumulative_raw, ax_cumulative_raw = plt.subplots(figsize=(10, 6))

ax_cumulative_raw.plot(
    years_range,
    house_data['Cumulative Investment (AUD)'],
    label='Cumulative House Investment',
    linestyle='--',
    color=color_palette['Cumulative Investment']
)

ax_cumulative_raw.plot(
    years_range,
    house_data['Equity (AUD)'],
    label='House Equity',
    marker='s',
    color=color_palette['House Investment']
)

ax_cumulative_raw.plot(
    years_range,
    btc_data['Cumulative Investment (AUD)'],
    label='Cumulative BTC Investment',
    linestyle='--',
    color=color_palette['Cumulative Investment']
)

ax_cumulative_raw.plot(
    years_range,
    btc_data['BTC Investment Value (AUD)'],
    label='BTC Investment Value',
    marker='o',
    color=color_palette['BTC Investment']
)

ax_cumulative_raw.set_xlabel('Year')
ax_cumulative_raw.set_ylabel('Amount (AUD)')
ax_cumulative_raw.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_cumulative_raw.set_title('Cumulative Investment vs. Equity/Value Over Time (Raw Values)')
ax_cumulative_raw.legend()
ax_cumulative_raw.grid(True)

st.pyplot(fig_cumulative_raw)

st.write("""
**Figure 1:** *Cumulative Investment vs. Equity/Value Over Time (Raw Values)*

This chart compares the total amount invested over time against the raw equity from house ownership and the raw value of BTC investments. It provides a clear comparison of how much you've invested versus how much each investment has grown without considering inflation or taxes.
""")

# Additional Chart: Net Gain Over Time
st.subheader('Net Gain Over Time')

# Plot 2: Cumulative Investment vs. Equity/Value (Adjusted for Inflation and Taxes)
fig_cumulative_adjusted, ax_cumulative_adjusted = plt.subplots(figsize=(10, 6))

ax_cumulative_adjusted.plot(
    years_range,
    house_data['Inflation-Adjusted Equity (AUD)'],
    label='Inflation-Adjusted House Equity',
    marker='s',
    color=color_palette['Adjusted Equity']
)

ax_cumulative_adjusted.plot(
    years_range,
    btc_data['Inflation & Tax Adjusted BTC Value (AUD)'],
    label='Inflation & Tax Adjusted BTC Value',
    marker='o',
    color=color_palette['Adjusted BTC Value']
)

ax_cumulative_adjusted.set_xlabel('Year')
ax_cumulative_adjusted.set_ylabel('Amount (AUD in Today\'s Dollars)')
ax_cumulative_adjusted.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_cumulative_adjusted.set_title('Cumulative Investment vs. Equity/Value Over Time (Adjusted for Inflation and Taxes)')
ax_cumulative_adjusted.legend()
ax_cumulative_adjusted.grid(True)

st.pyplot(fig_cumulative_adjusted)

st.write("""
**Figure 2:** *Cumulative Investment vs. Equity/Value Over Time (Adjusted for Inflation and Taxes)*

This chart compares the inflation and tax-adjusted equity from house ownership against the inflation and tax-adjusted value of BTC investments. It provides insight into the real value of your investments by accounting for the diminishing purchasing power of money and tax implications.
""")


st.write("""
Net gain represents the adjusted equity or value minus the cumulative investment. It effectively shows your profit after accounting for all the money you've invested.
""")

house_net_gain = house_data['Inflation-Adjusted Equity (AUD)'] - house_data['Cumulative Investment (AUD)']
btc_net_gain = btc_data['Inflation & Tax Adjusted BTC Value (AUD)'] - btc_data['Cumulative Investment (AUD)']

fig_net_gain, ax_net_gain = plt.subplots(figsize=(10, 6))
ax_net_gain.plot(years_range, house_net_gain, label='House Net Gain', marker='s', color=color_palette['Adjusted Equity'])
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

# Additional Chart: Total Costs of Owning a House vs. Renting
st.subheader('Total Costs: Owning a House vs. Renting')

st.write("""
Comparing the total costs associated with owning a house (interest payments and property costs) to renting can help you understand the financial commitments of each option.
We started off with the assumption that the rent amount was equal to the interest portion of the mortgage payment, and over time the costs diverge as rent and property costs increase with inflation.
Note, these don't factor in changing future market conditions other than inflation.
""")

total_house_ownership_costs = [
    interest + cost 
    for interest, cost in zip(
        house_data['Annual Interest (AUD)'].cumsum(),
        annual_costs_list
    )
]

fig_total_costs, ax_total_costs = plt.subplots(figsize=(10, 6))
ax_total_costs.plot(
    years_range,
    total_house_ownership_costs,
    label='Total House Ownership Costs',
    marker='s',
    color=color_palette['House Investment']
)
ax_total_costs.plot(
    years_range,
    cumulative_rent,
    label='Cumulative Rent Costs',
    marker='^',
    color=color_palette['Rent Paid']
)
ax_total_costs.set_xlabel('Year')
ax_total_costs.set_ylabel('Total Costs (AUD)')
ax_total_costs.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_total_costs.set_title('Total Costs: House Ownership vs. Renting')
ax_total_costs.legend()
ax_total_costs.grid(True)
st.pyplot(fig_total_costs)

st.write("""
This chart compares the total costs of house ownership (including mortgage interest and property costs) versus renting over time. While house ownership builds equity, it's important to understand the total costs involved in each option.
""")

# Effect of Inflation and CGT on Bitcoin Investment
st.subheader('Effect of Capital Gains Tax on Bitcoin Investment')

st.write("""
Understanding how capital gains tax (CGT) impacts your Bitcoin investment is crucial. This chart shows the raw Bitcoin investment value and the value after capital gains tax.

It's important to remember that you only pay the CGT if you sell. If you decide to not sell and continue investing, your wealth may continue to grow.
""")

fig_cgt, ax_cgt = plt.subplots(figsize=(10, 6))
ax_cgt.plot(years_range, btc_values, label='Raw BTC Value', linestyle='--', color=color_palette['BTC Investment'])
ax_cgt.plot(years_range, btc_after_tax_values, label='After CGT', marker='o', color=color_palette['Adjusted BTC Value'])
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

st.divider()

########################################################
# Purchasing Power and Inflation

st.subheader('Purchasing Power and Inflation')

st.write("""
Inflation reduces the purchasing power of money over time, affecting both cash and investments. To understand the real value of your investments, it's important to adjust for inflation.

In this section, we'll compare both the raw and inflation-adjusted values of your house equity and Bitcoin investment to provide a clear picture of their real growth.
""")

fig_inflation, ax_inflation = plt.subplots(figsize=(10, 6))

# Plot Inflation-Adjusted Values
ax_inflation.plot(
    years_range,
    house_data['Inflation-Adjusted Equity (AUD)'],
    label='Inflation-Adjusted House Equity',
    marker='s',
    color=color_palette['Adjusted Equity']
)
ax_inflation.plot(
    years_range,
    btc_purchasing_power_values,
    label='Inflation & Tax Adjusted BTC Value',
    marker='o',
    color=color_palette['Adjusted BTC Value']
)

# Plot Raw Values
ax_inflation.plot(
    years_range,
    house_data['Equity (AUD)'],
    label='Raw House Equity',
    linestyle='--',
    marker='s',
    color=color_palette['House Investment']
)
ax_inflation.plot(
    years_range,
    btc_data['BTC Investment Value (AUD)'],
    label='Raw BTC Investment Value',
    linestyle='--',
    marker='o',
    color=color_palette['BTC Investment']
)

ax_inflation.set_xlabel('Year')
ax_inflation.set_ylabel('Value (AUD)')
ax_inflation.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax_inflation.set_title('Purchasing Power and Raw Investment Values Over Time')
ax_inflation.legend()
ax_inflation.grid(True)

st.pyplot(fig_inflation)

st.write("""
This chart displays both the raw and inflation-adjusted values of your house equity and Bitcoin investments. The raw values show the nominal growth of your investments, while the inflation-adjusted values reflect their real purchasing power in today's dollars.
""")

# House Price in Bitcoin and AUD Over Time
st.subheader('House Price in Bitcoin and AUD Over Time')

fig4, ax4 = plt.subplots(figsize=(10, 6))

# Plot house price in BTC on the primary y-axis (left)
ax4.plot(
    years_range,
    house_price_in_btc,
    label='House Price in BTC',
    marker='^',
    color=color_palette['House Price in BTC']
)
ax4.set_xlabel('Year')
ax4.set_ylabel('House Price (BTC)', color=color_palette['House Price in BTC'])
ax4.tick_params(axis='y', labelcolor=color_palette['House Price in BTC'])

# Create a secondary y-axis (right)
ax4b = ax4.twinx()

# Plot house price in AUD on the secondary y-axis
ax4b.plot(
    years_range,
    house_values,
    label='House Price in AUD',
    marker='o',
    color=color_palette['House Investment']
)
ax4b.set_ylabel('House Price (AUD)', color=color_palette['House Investment'])
ax4b.tick_params(axis='y', labelcolor=color_palette['House Investment'])
ax4b.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))

# Combine legends from both axes
lines, labels = ax4.get_legend_handles_labels()
lines2, labels2 = ax4b.get_legend_handles_labels()
ax4b.legend(lines + lines2, labels + labels2, loc='upper left')

ax4.set_title('House Price in Bitcoin and AUD Over Time')
ax4.grid(True)

st.pyplot(fig4)

st.write("""
This chart shows how many Bitcoins would be required to purchase the house over time (left y-axis) and the house price in AUD (right y-axis). If Bitcoin appreciates faster than the house price, the number of Bitcoins needed decreases, enhancing your purchasing power relative to the housing market.
""")

# Conclusion
st.header('Conclusion')

final_btc_value = btc_purchasing_power_values[-1]
final_house_equity = inflation_adjusted_house_equity[-1]

if final_btc_value > final_house_equity:
    st.write(f"By investing in Bitcoin, you could potentially have **\${final_btc_value:,.0f}** in adjusted value after {years_simulated} years, compared to **\${final_house_equity:,.0f}** in house equity.")
    st.write("Investing in Bitcoin might be a viable alternative to purchasing a house, especially if housing affordability is a concern in the short term. You can start buying Bitcoin today and transfer it into a house when it better suits your needs.")
else:
    st.write(f"By purchasing a house, you could potentially have **\${final_house_equity:,.0f}** in adjusted equity after {years_simulated} years, compared to **\${final_btc_value:,.0f}** from investing in Bitcoin.")
    st.write("Purchasing a house could be a better investment over the long term.")

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
