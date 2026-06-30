"""
AgriSense AI — Streamlit Dashboard
Main entry point for the decision-support platform.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="AgriSense AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ----
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2e7d32;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.5rem 0;
    }
    .risk-low { color: #2e7d32; font-weight: 700; }
    .risk-medium { color: #f57f17; font-weight: 700; }
    .risk-high { color: #c62828; font-weight: 700; }
    .info-box {
        background: #f5f5f5;
        border-left: 4px solid #2e7d32;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.75rem 0;
    }
    .divider {
        border-top: 2px solid #e0e0e0;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.image("https://img.icons8.com/color/96/tractor.png", width=64)
    st.markdown("## 🌱 AgriSense AI")
    st.markdown("*Explainable AI for Agricultural Finance — Swedish Demo*")
    st.markdown("---")

    # Role selector (demo toggle)
    role = st.radio(
        "👤 View as:",
        ["🏦 Loan Officer", "👨‍🌾 Farmer"],
        horizontal=True,
    )

    st.markdown("---")

    # Navigation
    st.markdown("### 📋 Navigation")
    page = st.radio(
        "Go to:",
        [
            "🏠 Dashboard",
            "👨‍🌾 Farmer Profile",
            "📄 Documents",
            "💰 Financial Analysis",
            "🏦 Existing Loans",
            "🌦️ External Risk",
            "🤖 AI Prediction",
            "🔮 Scenario Analysis",
            "📝 Decision Memo",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("v1.0.0 | AgriSense AI")
    st.caption("Synthetic data only | GDPR compliant")

# ---- Header ----
st.markdown(
    '<p class="main-header">🌱 AgriSense AI</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-header">'
    'Transforming fragmented financial, operational, and environmental data '
    'into explainable AI-powered decision support.'
    '</p>',
    unsafe_allow_html=True,
)

# ---- API Base URL ----
API_BASE = "http://localhost:8000/api"
FARMER_ID = 1  # Default demo farmer

# ---- Import and render the selected page ----
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def fetch_json(endpoint: str):
    """Fetch data from the FastAPI backend."""
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.warning(f"⚠️ Backend not reachable at {API_BASE}{endpoint}: {e}")
        return None


def risk_badge(level: str) -> str:
    """Return colored HTML for risk level."""
    colors = {"low": "#2e7d32", "medium": "#f57f17", "high": "#c62828"}
    color = colors.get(level, "#666")
    return f'<span style="color:{color};font-weight:700;text-transform:uppercase;">{level}</span>'


# ===========================================================================
# Page: Dashboard
# ===========================================================================
if page == "🏠 Dashboard":
    st.markdown("## 📊 Portfolio Overview")

    col1, col2, col3, col4 = st.columns(4)

    # Fetch farmer data
    farmer_data = fetch_json(f"/farmers/{FARMER_ID}")

    if farmer_data:
        with col1:
            st.metric("Farmer", farmer_data.get("full_name", "N/A"))
        with col2:
            st.metric("UC Score", farmer_data.get("cibil_score", "N/A"))
        with col3:
            st.metric("State", farmer_data.get("state", "NA"))
        with col4:
            st.metric("Farming Experience", f"{farmer_data.get('years_in_farming', 'N/A')} years")

    # Latest prediction
    pred_data = fetch_json(f"/farmers/{FARMER_ID}/predictions")
    if pred_data and len(pred_data) > 0:
        latest = pred_data[0]

        st.markdown("---")
        st.markdown("### 🤖 Latest AI Assessment")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            risk = latest.get("overall_financing_risk", "N/A")
            st.markdown(
                f'<div class="metric-card">'
                f'<small>Overall Risk</small><br>'
                f'{risk_badge(risk)}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col2:
            score = latest.get("credit_risk_score", 0)
            delta_color = "inverse"
            st.metric("Credit Risk Score", f"{score:.0%}",
                      delta="Low" if score < 0.3 else "Medium" if score < 0.55 else "High",
                      delta_color=delta_color)

        with col3:
            repay = latest.get("repayment_probability", 0)
            st.metric("Repayment Probability", f"{repay:.0%}")

        with col4:
            capacity = latest.get("debt_capacity", 0)
            st.metric("Additional Debt Capacity", f"{capacity:,.0f} kr")

        # Risk breakdown
        st.markdown("---")
        st.markdown("### 🎯 Risk Breakdown")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fr = latest.get("financial_health_risk", "N/A")
            st.markdown(f"**Financial Health**<br>{risk_badge(fr)}", unsafe_allow_html=True)
        with col2:
            er = latest.get("environmental_risk", "N/A")
            st.markdown(f"**Environmental**<br>{risk_badge(er)}", unsafe_allow_html=True)
        with col3:
            mr = latest.get("market_risk", "N/A")
            st.markdown(f"**Market**<br>{risk_badge(mr)}", unsafe_allow_html=True)
        with col4:
            or_ = latest.get("overall_financing_risk", "N/A")
            st.markdown(f"**Overall Financing**<br>{risk_badge(or_)}", unsafe_allow_html=True)

        # Feature Importance
        if latest.get("feature_importance_json"):
            import json
            fi = json.loads(latest["feature_importance_json"])
            fi_df = pd.DataFrame({
                "Feature": list(fi.keys()),
                "Importance": list(fi.values()),
            }).sort_values("Importance", ascending=True).tail(10)

            st.markdown("### 📈 Top Feature Importance")
            fig = px.bar(fi_df, x="Importance", y="Feature", orientation="h",
                         color="Importance", color_continuous_scale="Greens")
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("👈 Run a prediction first from the 'AI Prediction' page.")


# ===========================================================================
# Page: Farmer Profile
# ===========================================================================
elif page == "👨‍🌾 Farmer Profile":
    st.markdown("## 👨‍🌾 Farmer Profile")

    farmer_data = fetch_json(f"/farmers/{FARMER_ID}")

    if farmer_data:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Personal Information")
            st.markdown(f"**Name:** {farmer_data.get('full_name')}")
            st.markdown(f"**Email:** {farmer_data.get('email', 'N/A')}")
            st.markdown(f"**Phone:** {farmer_data.get('phone', 'N/A')}")
            st.markdown(f"**Address:** {farmer_data.get('address', 'N/A')}")

        with col2:
            st.markdown("### Credit & Experience")
            uc = farmer_data.get("cibil_score", 0)
            st.metric("UC Score", uc)

            # UC Score gauge (Swedish credit bureau)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=uc,
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {"range": [300, 900]},
                    "bar": {"color": "#2e7d32" if uc >= 700 else "#f57f17" if uc >= 600 else "#c62828"},
                    "steps": [
                        {"range": [300, 600], "color": "#ffcdd2"},
                        {"range": [600, 700], "color": "#fff9c4"},
                        {"range": [700, 900], "color": "#c8e6c9"},
                    ],
                    "threshold": {"line": {"color": "black", "width": 2}, "value": 700},
                },
                title={"text": "UC Score Range"},
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"**Years in Farming:** {farmer_data.get('years_in_farming', 'N/A')}")
            st.markdown(f"**State:** {farmer_data.get('state', 'N/A')}")
            st.markdown(f"**District:** {farmer_data.get('district', 'N/A')}")

        # Operational overview
        ops_data = fetch_json(f"/farmers/{FARMER_ID}/operational")
        if ops_data and len(ops_data) > 0:
            ops = ops_data[0]
            st.markdown("---")
            st.markdown("### 🌾 Farm Operations")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Farm Size", f"{ops.get('farm_size_acres', 0):.1f} ha")
            with col2:
                st.metric("Crop", ops.get("crop_type", "N/A").replace("Wheat","Vete").replace("Barley","Korn"))
            with col3:
                st.metric("Land Ownership", ops.get("land_ownership", "N/A").title())
            with col4:
                st.metric("Insurance", "✅ Yes" if ops.get("has_insurance") else "❌ No")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tractor", "✅" if ops.get("has_tractor") else "❌")
            with col2:
                st.metric("Irrigation", "✅" if ops.get("has_irrigation") else "❌")
            with col3:
                land_val = ops.get("land_value_estimate", 0)
                st.metric("Land Value (Est.)", f"{land_val:,.0f} kr" if land_val else "N/A")


# ===========================================================================
# Page: Documents
# ===========================================================================
elif page == "📄 Documents":
    st.markdown("## 📄 Digital Farmer Vault")

    st.markdown("""
    <div class="info-box">
    All uploaded documents are stored securely. Each document is linked to the farmer
    and its extracted data is traced back to its source.
    </div>
    """, unsafe_allow_html=True)

    # Simulated document list (backend doesn't have a list endpoint yet — uses seed data)
    docs = [
        {"name": "Balance Sheet FY 2023-24", "type": "Financial Statement", "date": "2024-04-15", "status": "✅ Verified"},
        {"name": "Income Statement FY 2023-24", "type": "Financial Statement", "date": "2024-04-15", "status": "✅ Verified"},
        {"name": "Bank Statement (6 months)", "type": "Bank Statement", "date": "2024-06-01", "status": "✅ Verified"},
        {"name": "Farm Loan Agreement", "type": "Loan Document", "date": "2022-06-01", "status": "✅ Verified"},
        {"name": "Tractor Loan Agreement", "type": "Loan Document", "date": "2023-03-01", "status": "✅ Verified"},
        {"name": "Land Title Deed", "type": "Land Record", "date": "2010-01-15", "status": "✅ Verified"},
        {"name": "Crop Production Report", "type": "Farm Document", "date": "2024-05-30", "status": "✅ Verified"},
        {"name": "Crop Insurance Policy", "type": "Insurance", "date": "2024-01-01", "status": "✅ Active"},
    ]

    df = pd.DataFrame(docs)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📤 Upload New Document")
    st.info("Document upload will be available in the full version. For the demo, sample documents are pre-loaded.")


# ===========================================================================
# Page: Financial Analysis
# ===========================================================================
elif page == "💰 Financial Analysis":
    st.markdown("## 💰 Financial Analysis Engine")

    fa_data = fetch_json(f"/farmers/{FARMER_ID}/financial-analysis")

    if fa_data:
        ratios = fa_data.get("ratios", {})
        latest = fa_data.get("latest_financial", {})

        # Key metrics row
        st.markdown("### 📊 Key Financial Indicators")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            dti = ratios.get("debt_to_income", 0)
            dti_color = "inverse"
            st.metric("Debt-to-Income", f"{dti:.1%}",
                      delta="Good" if dti < 0.4 else "Elevated" if dti < 0.5 else "High",
                      delta_color=dti_color)

        with col2:
            dscr = ratios.get("dscr", 0)
            st.metric("DSCR", f"{dscr:.2f}x",
                      delta="Strong" if dscr >= 1.5 else "Adequate" if dscr >= 1.25 else "Weak")

        with col3:
            margin = ratios.get("operating_margin", 0)
            st.metric("Operating Margin", f"{margin:.1%}")

        with col4:
            ltv = ratios.get("loan_to_value", 0)
            st.metric("Loan-to-Value", f"{ltv:.1%}",
                      delta="Low" if ltv < 0.4 else "Moderate" if ltv < 0.6 else "High")

        # Detailed ratios
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 Profitability & Efficiency")
            st.metric("Working Capital", f"{ratios.get('working_capital', 0):,.0f} kr")
            st.metric("Current Ratio", f"{ratios.get('current_ratio', 0):.2f}x")
            st.metric("Cash Flow Margin", f"{ratios.get('cash_flow_margin', 0):.1%}")
            st.metric("Interest Coverage", f"{ratios.get('interest_coverage', 0):.2f}x")

            rpa = ratios.get("revenue_per_acre")
            if rpa:
                st.metric("Revenue per Hectare", f"{rpa:,.0f} kr")

        with col2:
            st.markdown("### 🏦 Leverage & Coverage")
            st.metric("Asset Coverage", f"{ratios.get('asset_coverage', 0):.2f}x")
            st.metric("Debt-to-Equity", f"{ratios.get('debt_to_equity', 0):.1%}")
            st.metric("Total Debt Service", f"{ratios.get('total_annual_debt_service', 0):,.0f}/yr")
            st.metric("Total Outstanding Debt", f"{ratios.get('total_outstanding_debt', 0):,.0f} kr")
            st.metric("EBITDA", f"{ratios.get('ebitda', 0):,.0f} kr")

        # Risk Flags
        flags = ratios.get("risk_flags", [])
        if flags:
            st.markdown("---")
            st.markdown("### ⚠️ Risk Flags")
            for flag in flags:
                sev = flag["severity"]
                icon = "🔴" if sev == "high" else "🟡"
                st.warning(f"{icon} **{flag['indicator']}**: {flag['message']}")

        health = ratios.get("overall_financial_health", "N/A")
        st.markdown(f"**Overall Financial Health:** {risk_badge(health)}", unsafe_allow_html=True)

        # Revenue trend from historical data
        financials = fetch_json(f"/farmers/{FARMER_ID}/financials")
        if financials:
            st.markdown("---")
            st.markdown("### 📈 Revenue & Income Trend")
            trend_df = pd.DataFrame([
                {"Year": str(f["year"]), "Revenue": f["revenue"], "Net Income": f["net_income"]}
                for f in sorted(financials, key=lambda x: x["year"])
            ])

            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df["Year"], y=trend_df["Revenue"],
                                 name="Revenue", marker_color="#2e7d32"))
            fig.add_trace(go.Scatter(x=trend_df["Year"], y=trend_df["Net Income"],
                                     name="Net Income", mode="lines+markers",
                                     line=dict(color="#1565c0", width=3)))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Financial data not available. Ensure the backend is running.")


# ===========================================================================
# Page: Existing Loans
# ===========================================================================
elif page == "🏦 Existing Loans":
    st.markdown("## 🏦 Existing Financing")

    loans_data = fetch_json(f"/farmers/{FARMER_ID}/loans")

    if loans_data:
        total_outstanding = sum(l.get("outstanding_balance", 0) for l in loans_data)
        total_monthly = sum(l.get("monthly_emi", 0) for l in loans_data)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Loans", len(loans_data))
        with col2:
            st.metric("Total Outstanding", f"{total_outstanding:,.0f} kr")
        with col3:
            st.metric("Monthly Amortering", f"{total_monthly:,.0f} kr")

        st.markdown("---")

        for loan in loans_data:
            with st.expander(
                f"{loan['loan_type'].replace('_', ' ').title()} — {loan['outstanding_balance']:,.0f}",
                expanded=True,
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Amount", f"{loan['original_amount']:,.0f} kr")
                    st.metric("Monthly Amortering", f"{loan['monthly_emi']:,.0f} kr")
                with col2:
                    st.metric("Outstanding", f"{loan['outstanding_balance']:,.0f} kr")
                    st.metric("Interest Rate", f"{loan['interest_rate']}%")
                with col3:
                    st.metric("Annual Debt Service", f"{loan['annual_debt_service']:,.0f} kr")
                    ratio = loan.get("repayment_ratio", 0)
                    st.metric("Repayment Record", f"{ratio:.0%}",
                              delta="On Track" if ratio >= 0.95 else "Delayed")

                # Repayment progress bar
                paid_pct = 1 - (loan["outstanding_balance"] / loan["original_amount"])
                st.progress(paid_pct, text=f"Repaid: {paid_pct:.0%}")
    else:
        st.info("No loan data available.")


# ===========================================================================
# Page: External Risk
# ===========================================================================
elif page == "🌦️ External Risk":
    st.markdown("## 🌦️ External Risk Factors")

    ext_data = fetch_json("/external-data")

    if ext_data:
        weather = ext_data.get("weather", {})
        commodity = ext_data.get("commodity", {})
        fuel = ext_data.get("fuel", {})

        st.markdown("### 🌧️ Weather Conditions")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rainfall", f"{weather.get('rainfall_mm', 0):.0f} mm")
        with col2:
            st.metric("Temperature", f"{weather.get('temperature_celsius', 0):.1f}°C")
        with col3:
            di = weather.get("drought_index", 0)
            st.metric("Drought Index", f"{di:.2f}",
                      delta="Low Risk" if di < 0.3 else "Moderate" if di < 0.6 else "High Risk")
        with col4:
            st.metric("Flood Risk", weather.get("flood_risk", "N/A").title())

        st.caption(f"Source: {weather.get('source', 'mock')} | Mock: {weather.get('is_mock', True)}")

        st.markdown("---")
        st.markdown("### 📈 Commodity Prices")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                commodity.get("commodity_name", "Wheat"),
                f"{commodity.get('commodity_price', 0):,.0f} kr",
                delta=f"{commodity.get('price_change_pct', 0):+.1f}%",
            )
        with col2:
            st.metric("Diesel", f"{fuel.get('diesel_price', 0):.2f}/L")
        with col3:
            st.metric("Fertilizer (NPK)", f"{fuel.get('fertilizer_urea', 0):.2f}/tonne")

        st.caption(f"Commodity source: {commodity.get('source', 'mock')}")

        st.markdown("---")
        st.markdown("### 🏛️ Government Support")
        subsidies = ext_data.get("government_subsidies", {})
        col1, col2 = st.columns(2)
        with col1:
            st.metric("EU CAP (Gardsstod)", f"{subsidies.get('pm_kisan', 0):,.0f}/yr")
        with col2:
            st.metric("CAP Greening", f"{subsidies.get('fertilizer_subsidy', 0):,.0f}/yr")

    else:
        st.warning("External data not available. Ensure the backend is running.")


# ===========================================================================
# Page: AI Prediction
# ===========================================================================
elif page == "🤖 AI Prediction":
    st.markdown("## 🤖 Explainable ML Prediction")

    st.markdown("""
    <div class="info-box">
    The Random Forest model predicts credit risk, repayment probability, and debt capacity.
    All predictions come with feature importance explanations.
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run Prediction", type="primary", use_container_width=True):
        with st.spinner("Running ML models..."):
            import requests as req
            try:
                resp = req.get(f"{API_BASE}/farmers/{FARMER_ID}/predict", timeout=30)
                if resp.status_code == 200:
                    st.success("✅ Prediction complete!")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Backend error: {e}")

    # Show latest prediction
    preds = fetch_json(f"/farmers/{FARMER_ID}/predictions")
    if preds and len(preds) > 0:
        pred = preds[0]

        st.markdown("---")
        st.markdown("### 📊 Prediction Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            score = pred.get("credit_risk_score", 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score * 100,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Credit Risk Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2e7d32" if score < 0.3 else "#f57f17" if score < 0.55 else "#c62828"},
                    "steps": [
                        {"range": [0, 30], "color": "#c8e6c9"},
                        {"range": [30, 55], "color": "#fff9c4"},
                        {"range": [55, 100], "color": "#ffcdd2"},
                    ],
                },
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            repay = pred.get("repayment_probability", 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=repay * 100,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Repayment Probability"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2e7d32" if repay > 0.7 else "#f57f17" if repay > 0.5 else "#c62828"},
                    "steps": [
                        {"range": [0, 50], "color": "#ffcdd2"},
                        {"range": [50, 70], "color": "#fff9c4"},
                        {"range": [70, 100], "color": "#c8e6c9"},
                    ],
                },
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col3:
            capacity = pred.get("debt_capacity", 0)
            st.markdown(
                f'<div class="metric-card" style="text-align:center;">'
                f'<small>Additional Debt Capacity</small><br>'
                f'<span style="font-size:2rem;font-weight:800;">{capacity:,.0f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            conf = pred.get("model_confidence", 0)
            st.metric("Model Confidence", f"{conf:.0%}")

        st.markdown(f"**Model Version:** {pred.get('model_version', 'N/A')}")
        st.markdown(f"**Overall Risk:** {risk_badge(pred.get('overall_financing_risk', 'N/A'))}",
                    unsafe_allow_html=True)


# ===========================================================================
# Page: Scenario Analysis
# ===========================================================================
elif page == "🔮 Scenario Analysis":
    st.markdown("## 🔮 Scenario Analysis")

    st.markdown("""
    <div class="info-box">
    Simulate "what-if" scenarios to understand how changes in weather, prices,
    or new loans affect the farmer's financial position.
    </div>
    """, unsafe_allow_html=True)

    scenario_type = st.selectbox(
        "Select Scenario",
        ["rainfall", "commodity", "new_loan", "interest", "fuel", "tractor_purchase"],
        format_func=lambda x: {
            "rainfall": "🌧️ Rainfall Change",
            "commodity": "📉 Commodity Price Drop",
            "new_loan": "💰 New Loan",
            "interest": "📈 Interest Rate Hike",
            "fuel": "⛽ Fuel Price Increase",
            "tractor_purchase": "🚜 Tractor Purchase",
        }.get(x, x),
    )

    params = {}
    if scenario_type == "rainfall":
        params["rainfall_change_pct"] = st.slider("Rainfall Change (%)", -50, 30, -20, 5)
    elif scenario_type == "commodity":
        params["price_change_pct"] = st.slider("Commodity Price Change (%)", -50, 30, -15, 5)
    elif scenario_type == "new_loan":
        params["loan_amount"] = st.number_input("Loan Amount ()", 50000, 2000000, 200000, 50000)
        params["interest_rate"] = st.slider("Interest Rate (%)", 5.0, 18.0, 10.0, 0.5)
        params["tenure_months"] = st.slider("Tenure (months)", 12, 120, 36, 12)
    elif scenario_type == "interest":
        params["rate_change_pct"] = st.slider("Interest Rate Increase (%)", 1, 10, 2, 1)
    elif scenario_type == "fuel":
        params["fuel_price_change_pct"] = st.slider("Fuel Price Increase (%)", 5, 50, 15, 5)
    elif scenario_type == "tractor_purchase":
        params["tractor_cost"] = st.number_input("Tractor Cost ()", 200000, 1500000, 500000, 50000)
        params["loan_amount"] = st.number_input("Loan Amount ()", 100000, 1500000, 400000, 50000)
        params["interest_rate"] = st.slider("Interest Rate (%)", 5.0, 15.0, 8.0, 0.5)

    if st.button("🔮 Run Scenario", type="primary", use_container_width=True):
        with st.spinner("Running scenario analysis..."):
            import requests as req
            try:
                resp = req.post(
                    f"{API_BASE}/scenarios",
                    json={"farmer_id": FARMER_ID, "scenario_type": scenario_type, "parameters": params},
                    timeout=30,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    st.success("✅ Scenario complete!")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Backend error: {e}")

    # Show past scenarios
    scenarios = fetch_json(f"/farmers/{FARMER_ID}/scenarios")
    if scenarios and len(scenarios) > 0:
        st.markdown("---")
        st.markdown("### 📊 Scenario History")

        for s in scenarios:
            with st.expander(f"{s['scenario_name']} — Risk: {s.get('risk_change', 'N/A').title()}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("New DTI", f"{s.get('new_debt_to_income', 0):.1%}" if s.get('new_debt_to_income') else "N/A")
                with col2:
                    st.metric("New DSCR", f"{s.get('new_dscr', 0):.2f}x" if s.get('new_dscr') else "N/A")
                with col3:
                    change = s.get("risk_change", "unchanged")
                    icon = "🔴" if change == "worsened" else "🟢" if change == "improved" else "🟡"
                    st.markdown(f"**Risk Impact:** {icon} {change.title()}")

                rec = s.get("recommendation")
                if rec:
                    st.info(rec)

    else:
        st.info("No scenarios run yet. Select a scenario above and click 'Run Scenario'.")


# ===========================================================================
# Page: Decision Memo
# ===========================================================================
elif page == "📝 Decision Memo":
    st.markdown("## 📝 AI Decision Memo")

    st.markdown("""
    <div class="info-box">
    The decision memo provides a structured summary for loan officers. It combines
    financial analysis, ML predictions, and Gemini AI explanations into one document.
    <strong>The final lending decision is always made by a human.</strong>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📝 Generate Decision Memo", type="primary", use_container_width=True):
        with st.spinner("Generating memo with Gemini AI..."):
            import requests as req
            try:
                resp = req.post(f"{API_BASE}/farmers/{FARMER_ID}/decision-memo", timeout=60)
                if resp.status_code == 200:
                    st.success("✅ Memo generated!")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Backend error: {e}")

    memos = fetch_json(f"/farmers/{FARMER_ID}/decision-memos")
    if memos and len(memos) > 0:
        memo = memos[0]

        if memo.get("full_memo"):
            st.markdown("---")
            st.code(memo["full_memo"], language=None)

        st.markdown("---")
        st.caption(f"Generated by: {memo.get('generated_by', 'N/A')} | "
                   f"Confidence: {memo.get('confidence_level', 'N/A')} | "
                   f"Date: {memo.get('created_at', 'N/A')}")
    else:
        st.info("No memo generated yet. Click 'Generate Decision Memo' above.")

# ---- Footer ----
st.markdown("---")
st.caption(
    "🌱 AgriSense AI — Explainable AI Decision Support for Agricultural Finance | "
    "For demo purposes only | The final lending decision is always made by a human."
)
