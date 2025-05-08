import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

# --- Title and Description ---
st.title("⚡ EV Charging Station Financial Model - Lagos (Dynamic)")
st.markdown("Model your EV station's cost, revenue, and return over time with dynamic projections, including revenue growth and cost inflation.")

# --- Sidebar Inputs ---
st.sidebar.header("📍 Station Configuration")
location = st.sidebar.selectbox("Station Location", ["Victoria Island", "Lekki", "Ikeja", "Agege"])
charger_type = st.sidebar.selectbox("Charger Type", ["AC (Slow)", "DC (Fast)"])
charging_time = st.sidebar.slider("Avg Charging Duration (mins)", 15, 120, 60)
sessions_per_day = st.sidebar.slider("Charging Sessions per Day", 10, 200, 50)

st.sidebar.header("💸 Cost Parameters")
capex = st.sidebar.number_input("Initial Setup Cost (₦)", min_value=1_000_000, value=15_000_000, step=1_000_000)
opex_monthly = st.sidebar.number_input("Monthly Operating Expense (₦)", min_value=50_000, value=500_000, step=50_000)

st.sidebar.header("⚡ Energy and Revenue")
if charger_type == "AC (Slow)":
    default_price = 300
else:
    default_price = 500
price_per_kwh = st.sidebar.number_input("Price per kWh (₦)", min_value=100, value=default_price, step=10)
avg_kwh_per_session = st.sidebar.slider("Avg kWh per Session", 5, 50, 20)
solar_percent = st.sidebar.slider("Solar Share (%)", 0, 100, 40)

opex_inflation = st.sidebar.slider("Annual Opex Inflation (%)", 0.0, 20.0, 5.0)
revenue_growth = st.sidebar.slider("Annual Revenue Growth (%)", 0.0, 20.0, 3.0)

st.sidebar.header("🏦 Financing")
loan_pct = st.sidebar.slider("Loan % of CapEx", 0, 100, 50)
loan_term = st.sidebar.slider("Loan Tenure (years)", 1, 10, 5)
interest_rate = st.sidebar.slider("Annual Interest Rate (%)", 0.0, 20.0, 10.0)
lease_option = st.sidebar.selectbox("Asset Ownership", ["Outright Purchase", "Lease"])

st.sidebar.header("📊 Projection")
years = st.sidebar.slider("Projection Duration (years)", 1, 15, 10)
discount_rate = st.sidebar.slider("Discount Rate (%)", 0.0, 20.0, 10.0)

# --- Calculations ---
sessions_per_year = sessions_per_day * 365
revenue_per_year = sessions_per_year * avg_kwh_per_session * price_per_kwh

loan_amount = capex * loan_pct / 100
equity_amount = capex - loan_amount
annual_loan_payment = npf.pmt(interest_rate / 100, loan_term, -loan_amount)
opex_yearly = opex_monthly * 12
lease_payment = capex * 0.15 if lease_option == "Lease" else 0

# Initialize lists
cash_flows = [-capex]
cumulative_cf = [-capex]
chart_years = []
chart_revenue = []
chart_costs = []
chart_net = []

annual_revenue = revenue_per_year
annual_opex = opex_yearly

for year in range(1, years + 1):
    # Apply growth and inflation
    annual_revenue *= (1 + revenue_growth / 100)
    annual_opex *= (1 + opex_inflation / 100)
    
    # Energy cost (simple estimate, could expand by energy mix)
    energy_cost = annual_revenue * 0.3  # assume 30% of revenue goes to energy cost

    # Loan payment drops off after loan term
    annual_costs = annual_opex + energy_cost + (annual_loan_payment if year <= loan_term else 0) + lease_payment

    net_cash = annual_revenue - annual_costs
    cash_flows.append(net_cash)

    chart_years.append(year)
    chart_revenue.append(annual_revenue)
    chart_costs.append(annual_costs)
    chart_net.append(net_cash)

    cumulative_cf.append(cumulative_cf[-1] + net_cash)

# Financial Metrics
npv = npf.npv(discount_rate / 100, cash_flows)
irr = npf.irr(cash_flows)
pi = (npv + capex) / capex
pbp = next((i for i, x in enumerate(cumulative_cf) if x > 0), "Beyond projection")
breakeven_price = (annual_opex + lease_payment + (annual_loan_payment if loan_term > 0 else 0)) / (sessions_per_year * avg_kwh_per_session)

# --- Output Section ---
st.subheader("💰 Financial Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("NPV (₦)", f"{npv:,.0f}")
col2.metric("IRR (%)", f"{irr * 100:.2f}" if irr else "N/A")
col3.metric("Payback Period", f"{pbp} years" if isinstance(pbp, int) else "Not achieved")
col4.metric("Profitability Index", f"{pi:.2f}")

st.subheader("🔑 Breakeven Price")
st.write(f"Minimum price per kWh to cover costs: ₦{breakeven_price:,.2f}")

# --- Cash Flow Table ---
df = pd.DataFrame({
    "Year": [0] + chart_years,
    "Cash Flow (₦)": cash_flows,
    "Cumulative CF (₦)": cumulative_cf
})
st.subheader("📆 Cash Flow Projection")
st.dataframe(df)

# --- Chart ---
st.subheader("📈 Revenue vs Cost (Dynamic Over Time)")
chart_df = pd.DataFrame({
    "Year": chart_years,
    "Revenue (₦)": chart_revenue,
    "Cost (₦)": chart_costs,
    "Net Cash Flow (₦)": chart_net
})
st.line_chart(chart_df.set_index("Year"))

# --- Notes ---
st.markdown("---")
st.markdown("**Tip:** Use the annual revenue growth and opex inflation sliders to simulate more realistic projections over time.")
