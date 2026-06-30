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
            "🏦 Applications",
            "� Data Quality",
            "�👨‍🌾 Farmer Profile",
            "📄 Documents",
            "💰 Financial Analysis",
            "🏦 Existing Loans",
            "🌦️ External Risk",
            "🤖 AI Prediction",
            "� Investment Simulator",
            "📝 Decision Memo",
            "🏗️ How It Works",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("v1.1.0 | AgriSense AI")
    st.caption("Synthetic data | GDPR compliant")

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
FARMER_ID = 2501  # Erik Johansson (demo farmer)

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

    # ---- AI Summary Card (#8) ----
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32);border-radius:12px;padding:1.25rem;margin-bottom:1rem;color:white;">
    <h3 style="margin:0;color:white;">🤖 AI Summary</h3>
    <p style="margin:0.5rem 0 0 0;font-size:0.95rem;opacity:0.95;">
    AI-generated overview of farmer financial health, risk profile, and recommendation. Updated on each prediction.
    </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch data
    farmer_data = fetch_json(f"/farmers/{FARMER_ID}")
    fa_data = fetch_json(f"/farmers/{FARMER_ID}/financial-analysis")
    pred_data = fetch_json(f"/farmers/{FARMER_ID}/predictions")
    env_data = fetch_json("/environmental-score")

    if farmer_data and fa_data and pred_data and len(pred_data) > 0:
        latest = pred_data[0]
        ratios = fa_data.get("ratios", {})
        rec = ratios.get("recommendation_category", {})

        # ---- Composite Scores Row (#6, #7) ----
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            hs = ratios.get("composite_health_score", 0)
            color = "#2e7d32" if hs >= 70 else "#f57f17" if hs >= 50 else "#c62828"
            st.markdown(f"""
            <div style="text-align:center;padding:0.5rem;">
            <h2 style="color:{color};margin:0;">{hs}/100</h2>
            <small>Financial Health Score</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            es = env_data.get("total_score", 0) if env_data else 50
            ecolor = "#2e7d32" if es <= 30 else "#f57f17" if es <= 55 else "#c62828"
            st.markdown(f"""
            <div style="text-align:center;padding:0.5rem;">
            <h2 style="color:{ecolor};margin:0;">{es}/100</h2>
            <small>Environmental Risk</small>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            cat = rec.get("category", "N/A")
            ccolor = rec.get("color", "#666")
            st.markdown(f"""
            <div style="text-align:center;padding:0.5rem;">
            <h2 style="color:{ccolor};margin:0;font-size:1.2rem;">{cat}</h2>
            <small>Recommendation</small>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            conf = latest.get("model_confidence", 0.85)
            st.markdown(f"""
            <div style="text-align:center;padding:0.5rem;">
            <h2 style="color:#1565c0;margin:0;">{conf:.0%}</h2>
            <small>Model Confidence</small>
            </div>
            """, unsafe_allow_html=True)

        # ---- Recommendation reasoning (#3) ----
        if rec.get("reasoning"):
            bg = rec.get("color", "#666") + "15"
            st.markdown(f"""
            <div style="background:{bg};border-left:4px solid {rec.get('color','#666')};padding:0.75rem;border-radius:4px;margin:0.5rem 0;">
            <strong>{rec.get('category')}</strong>: {rec.get('reasoning')}
            </div>
            """, unsafe_allow_html=True)

        # ---- AI Summary Text (Gemini-generated placeholder) (#8) ----
        risk_level = latest.get("overall_financing_risk", "medium")
        summaries = {
            "low": f"✅ {farmer_data.get('full_name','Farmer')} has strong cash flow, low debt burden, and favorable environmental conditions. Overall recommendation: <strong>Proceed</strong> with standard monitoring.",
            "medium": f"⚠️ {farmer_data.get('full_name','Farmer')} shows adequate financial health with some risk factors. Overall recommendation: <strong>Proceed with conditions</strong> — crop insurance or partial collateral advised.",
            "high": f"🔴 {farmer_data.get('full_name','Farmer')} has elevated risk indicators requiring attention. Overall recommendation: <strong>Manual review required</strong> — detailed assessment of collateral and repayment capacity needed.",
        }
        st.info(summaries.get(risk_level, summaries["medium"]))

        # ---- Decision Readiness Scores ----
        readiness = fetch_json(f"/farmers/{FARMER_ID}/decision-readiness")
        if readiness:
            st.markdown("---")
            st.markdown("### 🛡️ Decision Readiness")

            summ = readiness.get("summary", {})
            level = readiness.get("decision_readiness", {}).get("level", "unknown")

            colors_level = {"ready": "#2e7d32", "reduced_confidence": "#f57f17", "insufficient": "#c62828"}
            lc = colors_level.get(level, "#666")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Decision Readiness", f"{summ.get('decision_readiness', 'N/A')}")
            with col2:
                st.metric("Evidence Quality", f"{summ.get('evidence_quality', 'N/A')}")
            with col3:
                st.metric("Data Freshness", f"{summ.get('freshness', 'N/A')}")
            with col4:
                st.metric("Completeness", f"{summ.get('completeness', 'N/A')}")

            # Readiness message
            msg = readiness.get("decision_readiness", {}).get("message", "")
            rec = readiness.get("decision_readiness", {}).get("recommendation", "")
            st.markdown(f"""
            <div style="border-left:4px solid {lc};padding:0.5rem 0.75rem;background:{lc}10;border-radius:4px;margin:0.5rem 0;">
            <strong style="color:{lc};">{level.replace('_',' ').title()}</strong><br>
            <small>{msg}</small><br>
            <small><em>{rec}</em></small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ---- Key Metrics + Timeline (#4) ----
        trends = ratios.get("trends", {})
        col1, col2, col3, col4, col5 = st.columns(5)

        trend_icons = {"up": "🟢 ↑", "down": "🔴 ↓", "flat": "🟡 →"}

        with col1:
            rev = fa_data.get("latest_financial", {}).get("revenue", 0)
            t = trends.get("revenue", "flat")
            st.metric("Revenue", f"{rev:,.0f} kr", delta=f"YoY {trend_icons.get(t,'')}")

        with col2:
            dti = ratios.get("debt_to_income", 0)
            t = trends.get("debt", "flat")
            st.metric("Debt-to-Income", f"{dti:.1%}", delta=f"Debt {trend_icons.get(t,'')}")

        with col3:
            dscr = ratios.get("dscr", 0)
            t = trends.get("dscr_trend", "flat")
            st.metric("DSCR", f"{dscr:.2f}x", delta=f"{trend_icons.get(t,'')}")

        with col4:
            cf = fa_data.get("latest_financial", {}).get("operating_cash_flow", 0)
            t = trends.get("cash_flow", "flat")
            st.metric("Cash Flow", f"{cf:,.0f} kr", delta=f"{trend_icons.get(t,'')}")

        with col5:
            ni = fa_data.get("latest_financial", {}).get("net_income", 0)
            t = trends.get("net_income", "flat")
            st.metric("Net Income", f"{ni:,.0f} kr", delta=f"{trend_icons.get(t,'')}")

        # ---- Feature Importance + Risk Breakdown ----
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 🎯 Risk Breakdown")
            for label, key in [
                ("Financial Health", "financial_health_risk"),
                ("Environmental", "environmental_risk"),
                ("Market", "market_risk"),
                ("Overall Financing", "overall_financing_risk"),
            ]:
                val = latest.get(key, "N/A")
                st.markdown(f"**{label}:** {risk_badge(val)}", unsafe_allow_html=True)

        with col2:
            if latest.get("feature_importance_json"):
                fi = json.loads(latest["feature_importance_json"])
                fi_df = pd.DataFrame({
                    "Feature": list(fi.keys()),
                    "Importance": list(fi.values()),
                }).sort_values("Importance", ascending=True).tail(8)
                st.markdown("### 📈 Top Features")
                fig = px.bar(fi_df, x="Importance", y="Feature", orientation="h",
                             color="Importance", color_continuous_scale="Greens")
                fig.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Run a prediction from the 'AI Prediction' page to see the dashboard.")


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

    # ---- Liquidity Stress Test ----
    st.markdown("---")
    st.markdown("### 💧 Seasonal Liquidity Stress Test")
    st.caption("Agriculture is seasonal. Annual DSCR doesn't show monthly cash gaps.")

    liq_data = fetch_json(f"/farmers/{FARMER_ID}/liquidity-stress-test")
    if liq_data:
        summary = liq_data.get("summary", {})
        rating = summary.get("liquidity_rating", "")
        rating_color = "#2e7d32" if "Strong" in rating else "#f57f17" if "Adequate" in rating or "Seasonal" in rating else "#c62828"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Negative Months", summary.get("total_negative_months", 0))
        with col2:
            st.metric("Lowest Balance", f"{summary.get('lowest_cumulative_balance', 0):,.0f} kr")
        with col3:
            st.metric("Working Capital Gap", f"{summary.get('working_capital_needed', 0):,.0f} kr")
        with col4:
            st.markdown(f"**Rating:** <span style='color:{rating_color}'>{rating}</span>", unsafe_allow_html=True)

        # Monthly cash flow chart
        months_data = liq_data.get("monthly_cash_flows", [])
        if months_data:
            df = pd.DataFrame(months_data)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["name"], y=df["revenue_in"], name="Revenue In", marker_color="#2e7d32"))
            fig.add_trace(go.Bar(x=df["name"], y=df["costs_out"], name="Costs Out", marker_color="#ef5350"))
            fig.add_trace(go.Scatter(x=df["name"], y=df["net_cash"], name="Net Cash", mode="lines+markers",
                                     line=dict(color="#1565c0", width=3)))
            fig.add_hline(y=0, line_dash="dash", line_color="#666")
            fig.update_layout(height=350, barmode="group", margin=dict(l=0, r=0, t=10, b=0),
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)

        # Commodity stress test
        stress = liq_data.get("commodity_stress_test", {})
        stress_icon = "✅" if stress.get("survives_without_deficit") else "⚠️"
        st.info(f"{stress_icon} **{stress.get('scenario')}**: {stress.get('recommendation')}")

        # Stress months detail
        stress_months = liq_data.get("stress_months", [])
        if stress_months:
            with st.expander(f"🔍 Stress Months Detail ({len(stress_months)} months with negative cash flow)"):
                for sm in stress_months:
                    st.markdown(
                        f"**{sm['name']}**: Revenue {sm['revenue_in']:,.0f} kr → "
                        f"Costs {sm['costs_out']:,.0f} kr → "
                        f"Loan {sm['loan_out']:,.0f} kr → "
                        f"**Net: {sm['net_cash']:+,.0f} kr** "
                        f"(Balance: {sm['cumulative_balance']:,.0f} kr)"
                    )


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
elif page == "� Investment Simulator":
    st.markdown("## 💡 Investment Simulator")
    st.markdown("""
    <div class="info-box">
    Simulate investment decisions and see their full financial impact.
    Combine investments with weather and market conditions to understand
    the complete picture before making a commitment.
    </div>
    """, unsafe_allow_html=True)

    # ---- Investment Presets ----
    st.markdown("### 🎯 Choose an Investment Scenario")

    presets = fetch_json("/investment-presets") or {}

    col1, col2, col3 = st.columns(3)
    selected_presets = {}

    preset_keys = list(presets.keys())
    for i, key in enumerate(preset_keys):
        preset = presets[key]
        col = [col1, col2, col3][i % 3]
        with col:
            if st.button(f"{preset['icon']} {preset['label']}", key=f"preset_{key}", use_container_width=True):
                selected_presets[key] = preset["scenarios"]
                st.session_state["selected_investment"] = key
                st.session_state["selected_scenarios"] = preset["scenarios"]

    st.markdown("---")

    # ---- Custom Scenario Builder ----
    with st.expander("⚙️ Custom Scenario Builder", expanded="selected_investment" not in st.session_state):
        st.markdown("#### Add scenarios to combine")

        custom_scenarios = []

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Financial**")
            if st.checkbox("New Farm Loan"):
                amt = st.number_input("Loan Amount (SEK)", 100000, 5000000, 500000, 50000, key="fl_amt")
                rate = st.slider("Interest Rate (%)", 3.0, 10.0, 5.0, 0.5, key="fl_rate")
                tenure = st.slider("Tenure (months)", 12, 240, 120, 12, key="fl_tenure")
                custom_scenarios.append({"type": "new_farm_loan", "params": {
                    "loan_amount": amt, "interest_rate": rate, "tenure_months": tenure}})

            if st.checkbox("Working Capital Loan"):
                wc_amt = st.number_input("Loan Amount (SEK)", 50000, 1000000, 200000, 25000, key="wc_amt")
                wc_rate = st.slider("Interest Rate (%)", 4.0, 12.0, 6.5, 0.5, key="wc_rate")
                custom_scenarios.append({"type": "working_capital_loan", "params": {
                    "loan_amount": wc_amt, "interest_rate": wc_rate, "tenure_months": 24}})

            if st.checkbox("Refinance Existing Loans"):
                new_rate = st.slider("New Interest Rate (%)", 2.0, 8.0, 4.2, 0.1, key="refi_rate")
                custom_scenarios.append({"type": "refinance", "params": {"new_rate": new_rate}})

        with col2:
            st.markdown("**Environmental & Market**")
            if st.checkbox("Rainfall Change"):
                rain_pct = st.slider("Rainfall Change (%)", -50, 30, -20, 5, key="rain_pct")
                custom_scenarios.append({"type": "rainfall_change", "params": {"rainfall_change_pct": rain_pct}})

            if st.checkbox("Commodity Price Drop"):
                comm_pct = st.slider("Price Change (%)", -50, 30, -15, 5, key="comm_pct")
                custom_scenarios.append({"type": "commodity_price", "params": {"price_change_pct": comm_pct}})

            if st.checkbox("Fuel Price Increase"):
                fuel_pct = st.slider("Fuel Increase (%)", 5, 50, 15, 5, key="fuel_pct")
                custom_scenarios.append({"type": "fuel_price", "params": {"fuel_price_change_pct": fuel_pct}})

        st.markdown("**Operational**")
        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox("Farm Expansion"):
                add_ha = st.number_input("Additional Hectares", 5, 100, 20, 5, key="exp_ha")
                custom_scenarios.append({"type": "farm_expansion", "params": {
                    "additional_hectares": add_ha, "land_cost_per_ha": 85000,
                    "loan_pct": 70, "interest_rate": 4.5, "tenure_months": 120}})

            if st.checkbox("Install Irrigation"):
                irr_cost = st.number_input("System Cost (SEK)", 100000, 1000000, 350000, 50000, key="irr_cost")
                custom_scenarios.append({"type": "install_irrigation", "params": {
                    "system_cost": irr_cost, "loan_pct": 80, "interest_rate": 5.0, "tenure_months": 48}})

        with col2:
            if st.checkbox("Crop Change"):
                new_crop = st.selectbox("New Crop", ["Hostvete", "Varkorn", "Havre", "Hostraps", "Arter"])
                custom_scenarios.append({"type": "crop_change", "params": {
                    "new_crop": new_crop, "yield_change_pct": 10, "price_factor": 1.15}})

            if st.checkbox("Build Storage Facility"):
                store_cost = st.number_input("Construction Cost (SEK)", 200000, 2000000, 500000, 50000, key="store_cost")
                custom_scenarios.append({"type": "build_storage", "params": {
                    "construction_cost": store_cost, "loan_pct": 60, "interest_rate": 4.8, "tenure_months": 84}})

    # ---- Run Simulation ----
    scenarios_to_run = st.session_state.get("selected_scenarios", []) or custom_scenarios

    if scenarios_to_run:
        st.markdown("---")
        scenario_desc = " + ".join(
            presets.get(st.session_state.get("selected_investment", ""), {}).get("label", s["type"])
            if st.session_state.get("selected_investment") else s["type"].replace("_", " ").title()
            for s in scenarios_to_run
        )
        st.markdown(f"**Active scenarios:** {scenario_desc}")

        if st.button("💡 Simulate Investment Impact", type="primary", use_container_width=True):
            with st.spinner("Running investment simulation..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/investment-simulator",
                        params={"farmer_id": FARMER_ID},
                        json=scenarios_to_run,
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        st.session_state["sim_result"] = result
                        st.success("✅ Simulation complete!")
                        st.rerun()
                    else:
                        st.error(f"Error: {resp.status_code} — {resp.text}")
                except Exception as e:
                    st.error(f"Backend error: {e}")

    # ---- Show Comparison Table ----
    sim_result = st.session_state.get("sim_result")
    if sim_result:
        st.markdown("---")
        st.markdown(f"### 📊 Investment Impact: {sim_result.get('scenario_name', '')}")

        before = sim_result.get("before", {})
        after = sim_result.get("after", {})
        changes = sim_result.get("changes", {})

        # Comparison table
        comp_data = []
        for label, key, fmt in [
            ("Existing Debt", "existing_debt", "kr"),
            ("Monthly Amortering", "monthly_emi", "kr"),
            ("Debt-to-Income", "debt_to_income", "%"),
            ("DSCR", "dscr", "x"),
            ("Working Capital", "working_capital", "kr"),
            ("Operating Margin", "operating_margin", "%"),
            ("Revenue", "revenue", "kr"),
            ("Net Income", "net_income", "kr"),
            ("Recommendation", "recommendation", "text"),
        ]:
            b = before.get(key, 0)
            a = after.get(key, 0)
            c = changes.get(key, 0)

            if fmt == "%":
                b_str = f"{b:.1%}" if isinstance(b, (int, float)) else str(b)
                a_str = f"{a:.1%}" if isinstance(a, (int, float)) else str(a)
                c_str = f"{c:+.1%}" if isinstance(c, (int, float)) else str(c)
            elif fmt == "x":
                b_str = f"{b:.2f}x" if isinstance(b, (int, float)) else str(b)
                a_str = f"{a:.2f}x" if isinstance(a, (int, float)) else str(a)
                c_str = f"{c:+.2f}x" if isinstance(c, (int, float)) else str(c)
            elif fmt == "kr":
                b_str = f"{b:,.0f} kr" if isinstance(b, (int, float)) else str(b)
                a_str = f"{a:,.0f} kr" if isinstance(a, (int, float)) else str(a)
                c_str = f"{c:+,.0f} kr" if isinstance(c, (int, float)) else str(c)
            else:
                b_str = str(b)
                a_str = str(a)
                c_str = str(c)

            # Change color
            if isinstance(c, (int, float)) and fmt != "text":
                if "debt" in key.lower() or "dti" in key.lower():
                    # Lower is better for debt metrics
                    color = "#c62828" if c > 0 else "#2e7d32" if c < 0 else "#666"
                else:
                    color = "#2e7d32" if c > 0 else "#c62828" if c < 0 else "#666"
            else:
                color = "#f57f17" if a_str != b_str else "#666"

            comp_data.append({
                "Metric": label, "Before": b_str, "After": a_str,
                "Change": f"<span style='color:{color};font-weight:700'>{c_str}</span>",
            })

        df = pd.DataFrame(comp_data)
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Risk change and narrative
        risk_change = sim_result.get("risk_change", "unchanged")
        icon = "🔴" if risk_change == "worsened" else "🟢" if risk_change == "improved" else "🟡"
        st.markdown(f"### {icon} Overall Impact: {risk_change.title()}")

        rec = sim_result.get("recommendation", "")
        if rec:
            st.info(rec)

    # ---- Scenario History ----
    st.markdown("---")
    past = fetch_json(f"/farmers/{FARMER_ID}/scenarios")
    if past and len(past) > 0:
        st.markdown("### 📜 Previous Simulations")
        for s in past[:5]:
            change = s.get("risk_change", "unchanged")
            icon = "🔴" if change == "worsened" else "🟢" if change == "improved" else "🟡"
            with st.expander(f"{icon} {s['scenario_name']}"):
                st.caption(s.get("recommendation", ""))
    else:
        st.caption("No previous simulations yet.")


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

        # ---- Provenance (#1) ----
        st.markdown("---")
        st.markdown("### 📋 Data Provenance")
        fa_data = fetch_json(f"/farmers/{FARMER_ID}/financial-analysis")
        if fa_data:
            prov = fa_data.get("ratios", {}).get("provenance", {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"Revenue source: {prov.get('revenue', 'Financial Statement')}")
            with col2:
                st.caption(f"Debt source: {prov.get('debt', 'Loan Statement')}")
            with col3:
                st.caption(f"Asset source: {prov.get('assets', 'Financial Statement')}")

        st.markdown("---")
        st.caption(f"Generated by: {memo.get('generated_by', 'N/A')} | "
                   f"Confidence: {memo.get('confidence_level', 'N/A')} | "
                   f"Date: {memo.get('created_at', 'N/A')}")

        # ---- Advisory disclaimer (#11) ----
        st.markdown("""
        <div style="background:#fff3e0;border-left:4px solid #f57f17;padding:0.75rem;border-radius:4px;margin-top:1rem;">
        <strong>⚠️ AI Recommendation</strong><br>
        <small>This recommendation is advisory and intended to support, not replace, human lending decisions.
        All final credit decisions must be made by qualified loan officers in accordance with
        their institution's credit policies and applicable regulations.</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No memo generated yet. Click 'Generate Decision Memo' above.")


# ===========================================================================
# Page: Bank Officer Applications (#10)
# ===========================================================================
elif page == "🏦 Applications":
    st.markdown("## 🏦 Loan Applications")

    apps_data = fetch_json("/bank/applications?limit=50")

    if apps_data:
        total = apps_data.get("total", 0)
        apps = apps_data.get("applications", [])

        st.markdown(f"**{total}** total applications in the system")

        # Summary stats
        low = sum(1 for a in apps if a.get("risk_level") == "low")
        med = sum(1 for a in apps if a.get("risk_level") == "medium")
        high = sum(1 for a in apps if a.get("risk_level") == "high")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🟢 Low Risk", low)
        with col2:
            st.metric("🟡 Medium Risk", med)
        with col3:
            st.metric("🔴 High Risk", high)

        st.markdown("---")

        # Applications table
        df = pd.DataFrame(apps)
        df = df.rename(columns={
            "name": "Farmer", "state": "Region", "crop": "Crop",
            "farm_size_ha": "Farm (ha)", "risk_level": "Risk",
            "status": "Status", "uc_score": "UC Score",
        })

        # Color-code the risk column
        def color_risk(val):
            if val == "low":
                return "background-color: #c8e6c9; color: #2e7d32; font-weight: 700"
            elif val == "medium":
                return "background-color: #fff9c4; color: #f57f17; font-weight: 700"
            elif val == "high":
                return "background-color: #ffcdd2; color: #c62828; font-weight: 700"
            return ""

        styled = df[["Farmer", "Region", "Crop", "Farm (ha)", "Risk", "Status", "UC Score"]].style
        styled = styled.map(color_risk, subset=["Risk"])

        st.dataframe(styled, use_container_width=True, hide_index=True,
                     column_config={"Farmer": st.column_config.TextColumn(width="medium")})

        st.markdown("---")
        st.markdown("### 👆 Click any farmer above and go to 'Farmer Profile' to see full details.")
        st.info(f"Showing {len(apps)} most recent applications. Total in database: {total}")
    else:
        st.warning("No applications data available. Ensure the backend is running.")


# ===========================================================================
# Page: How It Works (#9 — Architecture Diagram)
# ===========================================================================
elif page == "🏗️ How It Works":
    st.markdown("## 🏗️ How AgriSense AI Works")

    st.markdown("""
    <div class="info-box">
    AgriSense AI transforms fragmented farm data into explainable, AI-powered decision support for lenders.
    Every step is transparent. The final decision is always human.
    </div>
    """, unsafe_allow_html=True)

    # Architecture flow
    st.markdown("### 🔄 The Pipeline")

    steps = [
        ("📄", "Document Upload", "Farmer uploads financial statements, loan docs, land records, crop reports"),
        ("🔍", "Data Extraction", "Key values extracted: revenue, assets, outstanding debt, crop yield"),
        ("🔗", "Unified Profile", "Financial + Operational + External data merged into one profile"),
        ("📊", "Financial Analysis", "10+ ratios calculated: DTI, DSCR, LTV, working capital, margins"),
        ("🌦️", "External Data", "Weather, commodity prices, fuel costs, EU subsidies integrated"),
        ("🤖", "ML Prediction", "Random Forest predicts credit risk, repayment probability, debt capacity"),
        ("💡", "Explainability", "Feature importance shows why each prediction was made"),
        ("🔮", "Scenario Analysis", "What-if simulations: rainfall, prices, new loans, interest rates"),
        ("📝", "Decision Memo", "Gemini AI generates structured report with all evidence"),
        ("👤", "Human Decision", "Loan officer reviews all data and makes the final decision"),
    ]

    for icon, title, desc in steps:
        st.markdown(f"""
        <div style="display:flex;align-items:center;padding:0.5rem 0;border-bottom:1px solid #eee;">
        <div style="font-size:1.5rem;width:40px;">{icon}</div>
        <div style="flex:1;">
        <strong>{title}</strong><br>
        <small style="color:#666;">{desc}</small>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Tech stack
    st.markdown("### 🧱 Tech Stack")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Frontend**")
        st.markdown("- Streamlit (Python)")
        st.markdown("- Plotly charts")
        st.markdown("- 11 interactive pages")

        st.markdown("**Backend**")
        st.markdown("- FastAPI (Python)")
        st.markdown("- 18 REST endpoints")
        st.markdown("- Async external APIs")

    with col2:
        st.markdown("**Data**")
        st.markdown("- SQLite + SQLAlchemy")
        st.markdown("- 9 table schema")
        st.markdown("- 2,500 synthetic farmers")
        st.markdown("- 18,500+ total rows")

        st.markdown("**ML**")
        st.markdown("- Random Forest × 3")
        st.markdown("- 150 trees, depth 12")
        st.markdown("- 15 engineered features")

    with col3:
        st.markdown("**AI**")
        st.markdown("- Gemini API")
        st.markdown("- Explanations only")
        st.markdown("- Never makes decisions")

        st.markdown("**DevOps**")
        st.markdown("- Docker")
        st.markdown("- .env config")
        st.markdown("- GDPR compliant")

    st.markdown("---")
    st.markdown("### 🎯 Design Philosophy")
    st.markdown("""
    > **Every feature answers one of Oscar's six questions:**
    >
    > 1. Combine heterogeneous data? ✅ Unified Profile
    > 2. Transparent debt capacity? ✅ Financial Analysis + ML
    > 3. Scenario analysis? ✅ What-If Engine
    > 4. Weather/commodity integration? ✅ External Data APIs
    > 5. ML beyond traditional analysis? ✅ Random Forest + Feature Importance
    > 6. Practical decision-support tools? ✅ Dashboard + Decision Memo
    """)


# ===========================================================================
# Page: Data Quality Dashboard
# ===========================================================================
elif page == "📊 Data Quality":
    st.markdown("## 📊 Data Quality Dashboard")
    st.markdown("""
    <div class="info-box">
    Complete preprocessing pipeline: validation, missing values, duplicates,
    outliers, and ambiguity detection. Issues are flagged — never silently removed.
    </div>
    """, unsafe_allow_html=True)

    dq_data = fetch_json("/data-quality/overview?limit=50")
    farmer_dq = fetch_json(f"/farmers/{FARMER_ID}/data-quality")

    if dq_data:
        # Overview stats
        st.markdown("### 📈 Dataset Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Farmers Analyzed", dq_data.get("farmers_analyzed", 0))
        with col2:
            avg_q = dq_data.get("average_quality_score", 0)
            qc = "#2e7d32" if avg_q >= 80 else "#f57f17" if avg_q >= 60 else "#c62828"
            st.markdown(f'<h2 style="color:{qc};text-align:center;">{avg_q}/100</h2><small>Avg Quality Score</small>', unsafe_allow_html=True)
        with col3:
            st.metric("Validation Issues", dq_data.get("total_validation_issues", 0))
        with col4:
            st.metric("Outliers Found", dq_data.get("total_outliers", 0))
        with col5:
            st.metric("Missing Values", dq_data.get("total_missing_values", 0))

        # Quality distribution
        st.markdown("---")
        st.markdown("### 📊 Quality Distribution")
        dist = dq_data.get("quality_distribution", {})
        dist_df = pd.DataFrame({
            "Category": ["Excellent (90+)", "Good (70-89)", "Fair (50-69)", "Poor (<50)"],
            "Farmers": [
                dist.get("excellent_90plus", 0),
                dist.get("good_70_89", 0),
                dist.get("fair_50_69", 0),
                dist.get("poor_below_50", 0),
            ],
        })
        colors = ["#2e7d32", "#7cb342", "#f57f17", "#c62828"]
        fig = px.bar(dist_df, x="Category", y="Farmers", color="Category",
                     color_discrete_sequence=colors)
        fig.update_layout(height=300, showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # Per-farmer detail
    if farmer_dq:
        st.markdown("---")
        st.markdown(f"### 🔍 Farmer Detail: ID {FARMER_ID}")

        summary = farmer_dq.get("summary", {})

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Records", summary.get("total_records", 0))
        with col2:
            st.metric("Validation Errors", summary.get("validation_errors", 0))
        with col3:
            st.metric("Missing Values", summary.get("missing_values", 0))
        with col4:
            st.metric("Duplicates", summary.get("duplicates", 0))
        with col5:
            st.metric("Outliers", summary.get("outliers", 0))

        qs = summary.get("data_quality_score", 0)
        qc = "#2e7d32" if qs >= 80 else "#f57f17" if qs >= 60 else "#c62828"
        st.markdown(f"**Data Quality Score:** <span style='color:{qc};font-size:1.5rem;font-weight:700;'>{qs}/100</span>", unsafe_allow_html=True)

        # Issues detail
        if farmer_dq.get("validation"):
            with st.expander(f"🔴 Validation Errors ({len(farmer_dq['validation'])})", expanded=True):
                for v in farmer_dq["validation"][:10]:
                    icon = "🔴" if v.get("severity") == "high" else "🟡"
                    st.warning(f"{icon} **{v.get('field')}**: {v.get('message')} — _{v.get('action')}_")

        if farmer_dq.get("outliers"):
            with st.expander(f"⚠️ Outliers ({len(farmer_dq['outliers'])})", expanded=True):
                for o in farmer_dq["outliers"][:10]:
                    st.info(f"📊 **{o.get('field')}**: {o.get('message')} — _{o.get('action')}_")

        if farmer_dq.get("duplicates"):
            with st.expander(f"🔄 Duplicates ({len(farmer_dq['duplicates'])})"):
                for d in farmer_dq["duplicates"]:
                    st.warning(f"{d.get('message')} — _{d.get('action')}_")

        if farmer_dq.get("ambiguities"):
            with st.expander(f"⚡ Data Ambiguities ({len(farmer_dq['ambiguities'])})", expanded=True):
                for a in farmer_dq["ambiguities"]:
                    st.error(f"**{a.get('field')}**: {a.get('message')} — _{a.get('action')}_")

    # ML Pipeline info
    st.markdown("---")
    st.markdown("### 🔬 ML Pipeline")

    st.markdown("""
    <table style="width:100%;font-size:0.9rem;">
    <tr style="background:#e8f5e9;"><td><strong>Step</strong></td><td><strong>Method</strong></td><td><strong>Status</strong></td></tr>
    <tr><td>1. Validation</td><td>Rule-based checks (min/max bounds)</td><td>✅ Active</td></tr>
    <tr><td>2. Missing Values</td><td>Median/mode imputation + flag</td><td>✅ Active</td></tr>
    <tr><td>3. Duplicates</td><td>Hash-based detection</td><td>✅ Active</td></tr>
    <tr><td>4. Outliers</td><td>IQR method (flag only)</td><td>✅ Active</td></tr>
    <tr><td>5. Standardization</td><td>Currency, unit, date conversion</td><td>✅ Active</td></tr>
    <tr><td>6. Ambiguity</td><td>Cross-document field comparison</td><td>✅ Active</td></tr>
    <tr><td>7. Feature Engineering</td><td>15 derived features</td><td>✅ Active</td></tr>
    <tr style="background:#fff3e0;"><td>8. Scaling</td><td>NOT needed (RF is scale-invariant)</td><td>⏭️ Skipped by design</td></tr>
    <tr><td>9. Encoding</td><td>Label Encoding (tree-based)</td><td>✅ Active</td></tr>
    <tr><td>10. Train/Test</td><td>80/20 stratified split</td><td>✅ Active</td></tr>
    <tr><td>11. Cross-Validation</td><td>5-fold StratifiedKFold</td><td>✅ Active</td></tr>
    <tr><td>12. Hyperparameters</td><td>GridSearchCV (n_est, depth, split)</td><td>✅ Active</td></tr>
    <tr><td>13. Evaluation</td><td>Precision, Recall, F1, ROC-AUC, Confusion Matrix</td><td>✅ Active</td></tr>
    </table>
    """, unsafe_allow_html=True)

    # Show evaluation if available
    eval_data = fetch_json("/ml/evaluation")
    if eval_data:
        st.markdown("---")
        st.markdown("### 📈 Latest Model Evaluation")

        ev = eval_data.get("evaluation", {}).get("risk_classifier", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ROC-AUC", f"{ev.get('roc_auc', 0):.3f}")
        with col2:
            st.metric("Precision", f"{ev.get('precision', 0):.3f}")
        with col3:
            st.metric("Recall", f"{ev.get('recall', 0):.3f}")
        with col4:
            st.metric("F1 Score", f"{ev.get('f1_score', 0):.3f}")

        cm = ev.get("confusion_matrix", {})
        if cm:
            st.markdown("#### Confusion Matrix")
            cm_df = pd.DataFrame([
                ["TN: " + str(cm.get("true_negative", 0)), "FP: " + str(cm.get("false_positive", 0))],
                ["FN: " + str(cm.get("false_negative", 0)), "TP: " + str(cm.get("true_positive", 0))],
            ], index=["Actual: Low Risk", "Actual: High Risk"],
               columns=["Pred: Low Risk", "Pred: High Risk"])
            st.dataframe(cm_df, use_container_width=True)
            st.caption(ev.get("note", ""))

        # CV scores
        cv = eval_data.get("cross_validation", {})
        if cv:
            st.markdown(f"**Cross-Validation (5-fold):** Mean ROC-AUC = {cv.get('mean_roc_auc', 0):.3f} ± {cv.get('std_roc_auc', 0):.3f}")

        # Best params
        hp = eval_data.get("hyperparameter_search", {})
        if hp:
            st.markdown(f"**Best Hyperparameters:** {hp.get('best_params', {})}")

        # Scaling note
        st.info(eval_data.get("scaling_note", "").split("\n")[0])
st.caption(
    "🌱 AgriSense AI — Explainable AI Decision Support for Agricultural Finance | "
    "For demo purposes only | The final lending decision is always made by a human."
)
