import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title='The Math', layout="centered") 

st.title('Understanding the Math Behind the Calculations')

st.write("""
G'day! Let's break down the numbers behind our calculations because we want scrutiny.
""")

st.header('1. Lenders Mortgage Insurance (LMI) Calculation')

st.write("""
**Lenders Mortgage Insurance (LMI)** is like a safety net for the bank (not you) when you're borrowing a big chunk of the property's value. The key figure here is the **Loan to Value Ratio (LVR)**, which tells us how much of the property's price you're borrowing.

Imagine the LVR as a pie chart showing how much of the house you own outright and how much the bank owns. The formula is:

""")

st.latex(r'\text{LVR} = \frac{\text{Loan Amount}}{\text{Property Value}}')

st.write("""
Depending on how big your slice of the pie is (your deposit), the LMI varies:

- **If LVR ≤ 80%**: You're borrowing less than 80% of the property's value—no LMI needed!
- **If 80% < LVR ≤ 85%**: LMI is 0.5% of the loan amount.
- **If 85% < LVR ≤ 90%**: LMI is 1% of the loan amount.
- **If 90% < LVR ≤ 95%**: LMI is 2% of the loan amount.
- **If LVR > 95%**: LMI is 3% of the loan amount.

So, the more you borrow relative to the property's value, the more LMI you'll pay.
""")

# Example Chart for LMI vs LVR
st.subheader('Example: LMI Rate vs LVR')

st.write("""
Let's visualize how LMI varies with different LVRs.
""")

# Create data for LVR and corresponding LMI rates
lvr_values = np.linspace(0.7, 1.0, 100)
lmi_rates = []
for lvr in lvr_values:
    if lvr <= 0.8:
        lmi_rate = 0
    elif lvr <= 0.85:
        lmi_rate = 0.005
    elif lvr <= 0.9:
        lmi_rate = 0.01
    elif lvr <= 0.95:
        lmi_rate = 0.02
    else:
        lmi_rate = 0.03
    lmi_rates.append(lmi_rate * 100)  # Convert to percentage

fig_lmi, ax_lmi = plt.subplots()
ax_lmi.plot(lvr_values * 100, lmi_rates)
ax_lmi.set_xlabel('Loan to Value Ratio (LVR) %')
ax_lmi.set_ylabel('LMI Rate %')
ax_lmi.set_title('LMI Rate vs LVR')
ax_lmi.grid(True)
st.pyplot(fig_lmi)

st.write("""
As you can see, the LMI rate increases in steps as the LVR increases.
The values charged by banks might vary, but this chart is a good approximation.
""")

st.header('2. Figuring Out Your Mortgage Payments')

st.write("""
Time to tackle the mortgage. We use the standard loan payment formula to calculate your monthly payments, considering the loan amount, interest rate, and loan term.

The formula is:

""")

st.latex(r'P = L \times \frac{r (1 + r)^{n}}{(1 + r)^{n} - 1}')

st.write("""
Where:

- **\( P \)** is your monthly payment.
- **\( L \)** is the loan amount.
- **\( r \)** is the monthly interest rate (annual rate divided by 12).
- **\( n \)** is the total number of payments (loan term in years multiplied by 12).

In our app, we use the `numpy_financial` library's `pmt` function to compute this payment:

""")

st.code("monthly_payment = -npf.pmt(monthly_interest_rate, total_payments, loan_amount)")

st.write("""
Each month, your payment is split between paying off the interest and chipping away at the principal (the actual loan amount). Here's how we figure that out:

""")

st.latex(r'''
\begin{align*}
\text{Interest}_t &= B_{t-1} \times r \\
\text{Principal}_t &= P - \text{Interest}_t \\
B_t &= B_{t-1} - \text{Principal}_t
\end{align*}
''')

st.write("""
- **\( \text{Interest}_t \)**: Interest payment in month **t**.
- **\( B_{t-1} \)**: Outstanding balance before the payment.
- **\( P \)**: Monthly payment calculated earlier.
- **\( \text{Principal}_t \)**: Portion of the payment that reduces the loan balance.
- **\( B_t \)**: Outstanding balance after the payment.

The Interest is just an expense, paying the Principal is what reduces the amount you owe to the bank.
""")

# Example Chart for Mortgage Amortization
st.subheader('Example: Mortgage Balance Over Time')

st.write("""
Let's see how your mortgage balance decreases over time.

Suppose you have:

- **Loan Amount (L)**: $800,000
- **Annual Interest Rate**: 5%
- **Loan Term**: 30 years

First, calculate the monthly interest rate and total number of payments:
""")

loan_amount = 800000  # Example loan amount
annual_interest_rate = 5.0  # Example annual interest rate in percent
monthly_interest_rate = annual_interest_rate / 100 / 12
mortgage_term_years = 30
n_payments = mortgage_term_years * 12

st.latex(r'''
\begin{align*}
r &= \frac{5\%}{12} = 0.0041667 \\
n &= 30 \times 12 = 360 \text{ payments}
\end{align*}
''')

# Calculate monthly payment
P = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** n_payments) / ((1 + monthly_interest_rate) ** n_payments - 1)

st.write(f"""
Using the formula, your monthly payment **P** is calculated to be approximately **${P:,.2f}**.
""")

# Calculate balance over time
balances = []
balance = loan_amount
for i in range(1, n_payments + 1):
    interest = balance * monthly_interest_rate
    principal = P - interest
    balance -= principal
    balances.append(balance)

# Convert balances to yearly data
years = np.arange(0, mortgage_term_years + 1)  # Years from 0 to mortgage_term_years
annual_balances = [loan_amount] + balances[11::12]  # Starting balance plus balance at each year

# Plot mortgage balance over time
fig_balance, ax_balance = plt.subplots()
ax_balance.plot(years, annual_balances)
ax_balance.set_xlabel('Years')
ax_balance.set_ylabel('Mortgage Balance ($)')
ax_balance.set_title('Mortgage Balance Over Time')
ax_balance.grid(True)
st.pyplot(fig_balance)

st.write("""
Over time, your mortgage balance decreases as you make payments.
""")

st.header('3. How Your House Investment Grows Over Time')

st.subheader('3.1 House Value Over Time')

st.write("""
Property values tend to go up over time. We calculate the future value of your house using:

""")

st.latex(r'\text{House Value}_t = \text{House Price}_0 \times (1 + g)^t')

st.write("""
Where:

- **\( \text{House Value}_t \)** is the estimated value after **t** years.
- **\( \text{House Price}_0 \)** is what you paid for the house.
- **\( g \)** is the annual house price growth rate.

Suppose:

- **House Price**: $1,000,000
- **Annual Growth Rate**: 6%

""")

house_price_0 = 1000000  # Initial house price
g = 0.06  # Annual growth rate
years_house = np.arange(0, mortgage_term_years + 1)  # 0 to 30 years
house_values = house_price_0 * (1 + g) ** years_house

fig_house_value, ax_house_value = plt.subplots()
ax_house_value.plot(years_house, house_values)
ax_house_value.set_xlabel('Years')
ax_house_value.set_ylabel('House Value ($)')
ax_house_value.set_title('House Value Growth Over Time')
ax_house_value.grid(True)
st.pyplot(fig_house_value)

st.write("""
You can see how the house value increases over the years.
""")

st.subheader('3.2 Paying Down Your Mortgage')

st.write("""
As you make payments, your mortgage balance shrinks:

""")

st.latex(r'\text{Mortgage Balance}_t = \text{Mortgage Balance}_{t-1} - \text{Principal Payment}_t')

st.write("""
Each year, you owe the bank less and own more of your house, it's a bit like having a piggy bank.
""")

# Already calculated annual_balances in the previous section
annual_principal_payments = [P * 12 - (annual_balances[i-1] - annual_balances[i]) if i > 0 else 0 for i in range(len(annual_balances))]

st.subheader('3.3 Equity Over Time')

st.write("""
Your **equity** is how much of the house you truly own:

""")

st.latex(r'\text{Equity}_t = \text{House Value}_t - \text{Mortgage Balance}_t')

equity = np.array(house_values) - np.array(annual_balances)

fig_equity, ax_equity = plt.subplots()
ax_equity.plot(years_house, equity)
ax_equity.set_xlabel('Years')
ax_equity.set_ylabel('Equity ($)')
ax_equity.set_title('Equity in House Over Time')
ax_equity.grid(True)
st.pyplot(fig_equity)

st.write("""
Your equity grows over time as the house value increases and the mortgage balance decreases.
""")

st.subheader('3.4 Adjusting for Inflation')

st.write("""
Inflation affects the real value of money over time. To account for this, we adjust the house value and equity for inflation:

""")

st.latex(r'\text{Inflation-Adjusted Value}_t = \frac{\text{Value}_t}{(1 + i)^t}')

st.write("""
Where:

- **\( i \)** is the annual inflation rate.

Suppose the inflation rate is **3.5%**.

""")

inflation_rate = 0.035  # Inflation rate
inflation_adjusted_equity = equity / ((1 + inflation_rate) ** years_house)

fig_inflation_equity, ax_inflation_equity = plt.subplots()
ax_inflation_equity.plot(years_house, inflation_adjusted_equity)
ax_inflation_equity.set_xlabel('Years')
ax_inflation_equity.set_ylabel('Inflation-Adjusted Equity ($)')
ax_inflation_equity.set_title('Inflation-Adjusted Equity Over Time')
ax_inflation_equity.grid(True)
st.pyplot(fig_inflation_equity)

st.write("""
This shows the real purchasing power of your equity after accounting for inflation.
""")

st.header('4. Investing in Bitcoin Over the Years')

st.subheader('4.1 Bitcoin Price Growth')

st.write("""
Now, let's switch gears and talk about Bitcoin. We assume its price grows each year, but the growth rate slows down over time:

""")

st.latex(r'\text{Bitcoin Price}_t = \text{Bitcoin Price}_{t-1} \times (1 + g_t)')

st.write("""
Where:

- **\( g_t \)** is the growth rate in year **t** (it decreases each year).

Suppose:

- **Initial Bitcoin Price**: $90,000
- **Initial Growth Rate**: 25%
- **Final Growth Rate**: 5%
- **Simulation Period**: 30 years

We use a linear decrease in growth rate from 25% to 5% over 30 years.
""")

initial_btc_price = 90000
years_btc = np.arange(0, mortgage_term_years + 1)
initial_growth_rate = 0.25
final_growth_rate = 0.05
growth_rates = np.linspace(initial_growth_rate, final_growth_rate, len(years_btc))

btc_prices = [initial_btc_price]
for i in range(1, len(years_btc)):
    btc_price = btc_prices[-1] * (1 + growth_rates[i])
    btc_prices.append(btc_price)

fig_btc_price, ax_btc_price = plt.subplots()
ax_btc_price.plot(years_btc, btc_prices)
ax_btc_price.set_xlabel('Years')
ax_btc_price.set_ylabel('Bitcoin Price ($)')
ax_btc_price.set_title('Bitcoin Price Growth Over Time')
ax_btc_price.grid(True)
st.pyplot(fig_btc_price)

st.write("""
The Bitcoin price increases over time, but the growth rate slows down each year.
Now, let's just be clear. This is a super simplified model. There are so many factors that could affect the price of Bitcoin.
Why start with 25%? Well it's well bellow what we've seen in the past, but it's also safely above the 5% we'd expect from real estate, so we don't have to be overly optimistic.
There are really complex models out there by Hedge managers like Blackrock, Van Eck, and Microstrategy that we can look up to if we want.
""")

st.subheader('4.2 Bitcoin Investment Over Time')

st.write("""
Each year, you invest the amount equivalent to your annual principal payments and property costs into Bitcoin.

Assuming:

- **Initial Investment**: Your deposit of $200,000
- **Annual BTC Investment**: Annual principal payments + annual property costs
- **Annual Property Costs**: Starting at $5,000, adjusted for inflation
""")

# Calculate annual property costs adjusted for inflation
annual_property_costs = 5000
annual_costs_list = [annual_property_costs * ((1 + inflation_rate) ** t) for t in years_btc]

# Calculate annual principal payments from the mortgage schedule
annual_principal = []
for i in range(1, len(annual_balances)):
    principal_paid = annual_balances[i-1] - annual_balances[i]
    annual_principal.append(principal_paid)
annual_principal.insert(0, 0)  # For year 0

btc_investment_per_year = np.array(annual_principal) + np.array(annual_costs_list)

# Initialize BTC holdings
btc_holdings = []
total_btc = 200000 / initial_btc_price  # Initial investment
btc_holdings.append(total_btc)
cumulative_btc_investment = [200000]
for i in range(1, len(years_btc)):
    btc_purchased = btc_investment_per_year[i] / btc_prices[i]
    total_btc += btc_purchased
    btc_holdings.append(total_btc)
    cumulative_btc_investment.append(cumulative_btc_investment[-1] + btc_investment_per_year[i])

st.subheader('4.3 Bitcoin Investment Value Over Time')

st.write("""
The value of your Bitcoin investment is:

""")

st.latex(r'\text{BTC Value}_t = \text{Total BTC Holdings}_t \times \text{Bitcoin Price}_t')

btc_values = np.array(btc_holdings) * np.array(btc_prices)

fig_btc_value, ax_btc_value = plt.subplots()
ax_btc_value.plot(years_btc, btc_values)
ax_btc_value.set_xlabel('Years')
ax_btc_value.set_ylabel('Bitcoin Investment Value ($)')
ax_btc_value.set_title('Bitcoin Investment Value Over Time')
ax_btc_value.grid(True)
st.pyplot(fig_btc_value)

st.write("""
Your Bitcoin investment value grows over time due to both your increasing holdings and the price appreciation.
""")

st.subheader('4.4 Adjusting for Inflation and CGT')

st.write("""
To see the real value, we adjust for inflation and calculate the impact of Capital Gains Tax (CGT).

First, the taxable gain:

""")

st.latex(r'\text{Taxable Gain}_t = \max\left(0, \text{BTC Value}_t - \text{Cumulative BTC Investment}_t\right)')

st.write("""
Assuming a CGT rate of 20%:

""")

cgt_rate = 0.20
taxable_gain = np.maximum(0, btc_values - cumulative_btc_investment)
cgt = taxable_gain * cgt_rate
after_tax_btc_value = btc_values - cgt

st.write("""
Then, we adjust for inflation:

""")

st.latex(r'\text{Inflation-Adjusted BTC Value}_t = \frac{\text{After-Tax BTC Value}_t}{(1 + i)^t}')

inflation_adjusted_btc_value = after_tax_btc_value / ((1 + inflation_rate) ** years_btc)

fig_btc_adjusted, ax_btc_adjusted = plt.subplots()
ax_btc_adjusted.plot(years_btc, inflation_adjusted_btc_value)
ax_btc_adjusted.set_xlabel('Years')
ax_btc_adjusted.set_ylabel('Inflation-Adjusted BTC Value ($)')
ax_btc_adjusted.set_title('Inflation-Adjusted Bitcoin Value Over Time')
ax_btc_adjusted.grid(True)
st.pyplot(fig_btc_adjusted)

st.write("""
This shows the real purchasing power of your Bitcoin investment after accounting for taxes and inflation.
""")

st.header('5. Comparing the Two Paths')

st.subheader('5.1 Net Gain Over Time')

st.write("""
For the house:

""")

st.latex(r'\text{House Net Gain}_t = \text{Inflation-Adjusted Equity}_t - \text{Cumulative Investment}_t')

st.write("""

Where:

- **Cumulative Investment**: Deposit + Sum of annual principal payments and property costs.

For Bitcoin:

""")

st.write("""

st.latex(r'\text{BTC Net Gain}_t = \text{Inflation-Adjusted BTC Value}_t - \text{Cumulative BTC Investment}_t')

Let\'s calculate and compare the net gains.

""")

# Calculate cumulative house investment
cumulative_house_investment = [200000]  # Initial deposit
for i in range(1, len(years_house)):
    total_invested = cumulative_house_investment[-1] + annual_principal[i] + annual_costs_list[i]
    cumulative_house_investment.append(total_invested)

# Calculate net gains
house_net_gain = inflation_adjusted_equity - cumulative_house_investment
btc_net_gain = inflation_adjusted_btc_value - cumulative_btc_investment

fig_net_gain, ax_net_gain = plt.subplots()
ax_net_gain.plot(years_house, house_net_gain, label='House Net Gain')
ax_net_gain.plot(years_btc, btc_net_gain, label='BTC Net Gain')
ax_net_gain.set_xlabel('Years')
ax_net_gain.set_ylabel('Net Gain ($)')
ax_net_gain.set_title('Net Gain Comparison Over Time')
ax_net_gain.legend()
ax_net_gain.grid(True)
st.pyplot(fig_net_gain)

st.write("""
This chart compares your net gain from investing in a house versus Bitcoin over time.
""")

st.subheader('5.2 How Many Bitcoins to Buy a House?')

st.write("""
We can also see how the house price compares to Bitcoin over time:

""")

st.latex(r'\text{House Price in BTC}_t = \frac{\text{House Value}_t}{\text{Bitcoin Price}_t}')

st.write("""
This tells you how many Bitcoins you would need to buy the house at any given time.

""")

house_price_in_btc = np.array(house_values) / np.array(btc_prices)

fig_house_btc, ax_house_btc = plt.subplots()
ax_house_btc.plot(years_btc, house_price_in_btc)
ax_house_btc.set_xlabel('Years')
ax_house_btc.set_ylabel('House Price in BTC')
ax_house_btc.set_title('House Price in Bitcoin Over Time')
ax_house_btc.grid(True)
st.pyplot(fig_house_btc)

st.write("""
As Bitcoin\'s price grows faster than the house value, you need fewer Bitcoins to buy the house over time.
""")

st.header('6. Wrapping It Up')

st.write("""
By crunching these numbers, we can get a fair idea of which path might lead to a better financial outcome—buying a house or investing in Bitcoin. Remember, this is based on assumptions and estimates. The real world is a great spin bowler, so it's wise to stay informed and maybe have a yarn with a financial advisor, which I am not.

At the end of the day, whether you're more comfortable with bricks and mortar or digital assets, understanding the maths can help you make a choice that's right for you.

Feel free to adjust the parameters and see how different scenarios play out!
         
Cheers and keep your head up Australia!

""")

st.write("""
Head back to the [main page](app.py) to play around with the numbers yourself.
""")
