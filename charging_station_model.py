import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

# --- Title and Description ---
st.title("⚡ EV Charging Station Financial Model - Lagos")
st.markdown("Model your EV station's cost, revenue, and return based on assumptions like location, charger type, pricing, energy mix, and financing.")

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
price_per_kwh = st.sidebar.number_input("Price per kWh (₦)", min_value=100, value=200, step=10)
avg_kwh_per_session = st.sidebar.slider("Avg kWh per Session", 5, 50, 20)
solar_percent = st.sidebar.slider("Solar Share (%)", 0, 100, 40)
dg_percent = st.sidebar.slider("Diesel Generator Share (%)", 0, 100 - solar_percent, 30)
cng_percent = 100 - solar_percent - dg_percent

grid_cost_per_kwh = st.sidebar.number_input("Grid Cost per kWh (₦)", min_value=10, value=50, step=5)
dg_cost_per_kwh = st.sidebar.number_input("Diesel Cost per kWh (₦)", min_value=100, value=150, step=10)
solar_cost_per_kwh = st.sidebar.number_input("Solar Cost per kWh (₦)", min_value=5, value=20, step=5)
cng_cost_per_kwh = st.sidebar.number_input("CNG Cost per kWh (₦)", min_value=50, value=100, step=10)

st.sidebar.header("🏦 Financing")
asset_ownership = st.sidebar.selectbox("Asset Ownership", ["Outright Purchase", "Lease"])
loan_pct = st.sidebar.slider("Loan % of CapEx (if purchased)", 0, 100, 50)
loan_term = st.sidebar.slider("Loan Tenure (years)", 1, 10, 5)
interest_rate = st.sidebar.slider("Annual Interest Rate (%)", 0.0, 20.0, 10.0)

st.sidebar.header("📊 Projection")
years = st.sidebar.slider("Projection Duration (years)", 1, 10, 5)
discount_rate = st.sidebar.slider("Discount Rate (%)", 0.0, 20.0, 10.0)

# --- Calculations ---
sessions_per_year = sessions_per_day * 365
revenue_per_year = sessions_per_year * avg_kwh_per_session * price_per_kwh

# Weighted energy cost
avg_energy_cost_per_kwh = (
    (solar_percent / 100) * solar_cost_per_kwh +
    (dg_percent / 100) * dg_cost_per_kwh +
    (cng_percent / 100) * cng_cost_per_kwh +
    (max(0, 100 - solar_percent - dg_percent - cng_percent) / 100) * grid_cost_per_kwh
)
energy_cost_per_year = sessions_per_year * avg_kwh_per_session * avg_energy_cost_per_kwh

# Financing
if asset_ownership == "Outright Purchase":
    loan_amount = capex * loan_pct / 100
    equity_amount = capex - loan_amount
    annual_loan_payment = npf.pmt(interest_rate / 100, loan_term, -loan_amount)
    annual_lease_payment = 0
else:
    annual_loan_payment = 0
    annual_lease_payment = capex * 0.15  # assume 15% of asset cost as yearly lease cost

opex_yearly = opex_monthly * 12
costs_per_year = opex_yearly + annual_loan_payment + annual_lease_payment + energy_cost_per_year
net_cash_flow = revenue_per_year - costs_per_year

# Build Cash Flows List
cash_flows = [-capex]
for year in range(1, years + 1):
    cash = net_cash_flow
    cash_flows.append(cash)

# Financial Metrics
npv = npf.npv(discount_rate / 100, cash_flows)
irr = npf.irr(cash_flows)
pv_of_inflows = np.sum([cf / (1 + discount_rate / 100) ** yr for yr, cf in enumerate(cash_flows[1:], 1)])
pi = pv_of_inflows / capex if capex != 0 else np.nan
cumulative_cf = np.cumsum(cash_flows)
pbp = next((i for i, x in enumerate(cumulative_cf) if x > 0), "Beyond projection")

# Breakeven Price Recommendation
breakeven_price_per_kwh = costs_per_year / (sessions_per_year * avg_kwh_per_session) if sessions_per_year > 0 else 0

# --- Output Section ---
st.subheader("💰 Financial Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("NPV (₦)", f"{npv:,.0f}")
col2.metric("IRR (%)", f"{irr * 100:.2f}" if irr else "N/A")
col3.metric("Payback Period", f"{pbp} years" if isinstance(pbp, int) else "Not achieved")
col4.metric("Profitability Index", f"{pi:.2f}" if not np.isnan(pi) else "N/A")

# --- Breakeven Price ---
st.subheader("💡 Price Recommendation")
st.write(f"To break even, you need to charge at least ₦{breakeven_price_per_kwh:.2f} per kWh.")

# --- Cash Flow Table ---
st.subheader("📆 Cash Flow Projection")
df = pd.DataFrame({
    "Year": list(range(0, years + 1)),
    "Cash Flow (₦)": cash_flows,
    "Cumulative CF (₦)": cumulative_cf
})
st.dataframe(df)

# --- Chart ---
st.subheader("📈 Revenue vs Cost")
chart_df = pd.DataFrame({
    "Year": list(range(1, years + 1)),
    "Revenue (₦)": [revenue_per_year] * years,
    "Cost (₦)": [costs_per_year] * years,
    "Net Cash Flow (₦)": [net_cash_flow] * years
})
st.line_chart(chart_df.set_index("Year"))

# --- Notes ---
st.markdown("---")
st.markdown("**Tip:** Adjust energy mix, asset ownership, or pricing to improve financial performance. Use the breakeven price as a guide for setting tariffs.")
