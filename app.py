"""
AgriSense AI - Application Workflow Platform
One application, three perspectives.

Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib, time
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(page_title="AgriSense AI", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

# ═══════════════ MODEL ═══════════════
@st.cache_resource
def load_model():
    p = Path(__file__).resolve().parent / "agrisense_model_bundle.pkl"
    if p.exists(): return joblib.load(p)
    alt = Path("d:/Laptop/Downloads/My Projects/Own Ideas/Agri-Sense/data/models/credit_risk_model.pkl")
    if alt.exists():
        return {"models":{
            "credit_risk_classifier":joblib.load(alt),
            "repayment_regressor":joblib.load(str(alt).replace("credit_risk","repayment")),
            "debt_capacity_regressor":joblib.load(str(alt).replace("credit_risk","debt_capacity")),
        },"version":"1.1.0"}
    return None
bundle = load_model()
MODEL_OK = bundle is not None

# ═══════════════ DATA ═══════════════
APP_ID = "AG-2026-0001"
FARMER = {"name":"Erik Johansson","region":"Skane","district":"Lund","years":18,"uc":720,"ha":85,"crop":"Hostvete","insurance":True}
FIN = [
    {"y":2024,"rev":680000,"opex":420000,"int":45000,"dep":80000,"ni":135000,"ta":3200000,"tl":1400000,"ca":580000,"cl":320000,"ebitda":260000,"cfo":180000},
    {"y":2023,"rev":620000,"opex":395000,"int":48000,"dep":78000,"ni":99000,"ta":3100000,"tl":1480000,"ca":540000,"cl":310000,"ebitda":235000,"cfo":155000},
    {"y":2022,"rev":590000,"opex":380000,"int":50000,"dep":75000,"ni":85000,"ta":2950000,"tl":1550000,"ca":500000,"cl":300000,"ebitda":220000,"cfo":140000},
]
LOANS = [
    {"lender":"Landshypotek","amt":500000,"out":320000,"rate":4.5,"emi":8500,"tenure":120,"on_time":42,"due":48},
    {"lender":"Swedbank","amt":200000,"out":85000,"rate":5.2,"emi":4200,"tenure":60,"on_time":28,"due":30},
]
PIPELINE = [
    {"id":"AG-2026-0001","name":"Erik Johansson","region":"Skane","district":"Lund","status":"Ready","score":87,"dscr":1.32,"ha":85,"crop":"Hostvete","years":18,"uc":720},
    {"id":"AG-2026-0002","name":"Anna Nilsson","region":"Ostergotland","district":"Linkoping","status":"Ready","score":82,"dscr":1.45,"ha":120,"crop":"Varvete","years":22,"uc":780},
    {"id":"AG-2026-0003","name":"Lars Persson","region":"Vastra Gotaland","district":"Skovde","status":"Pending Docs","score":65,"dscr":0.95,"ha":65,"crop":"Havre","years":8,"uc":610},
    {"id":"AG-2026-0004","name":"Maria Andersson","region":"Halland","district":"Falkenberg","status":"Needs Review","score":58,"dscr":0.78,"ha":45,"crop":"Varkorn","years":5,"uc":550},
    {"id":"AG-2026-0005","name":"Johan Karlsson","region":"Skane","district":"Ystad","status":"Ready","score":91,"dscr":1.85,"ha":150,"crop":"Hostvete","years":25,"uc":820},
    {"id":"AG-2026-0006","name":"Karin Svensson","region":"Uppsala","district":"Enkoping","status":"Submitted","score":88,"dscr":1.52,"ha":95,"crop":"Hostraps","years":15,"uc":740},
    {"id":"AG-2026-0007","name":"Peter Larsson","region":"Kalmar","district":"Vastervik","status":"Rejected","score":42,"dscr":0.55,"ha":30,"crop":"Havre","years":3,"uc":480},
    {"id":"AG-2026-0008","name":"Sofia Berg","region":"Varmland","district":"Karlstad","status":"In Progress","score":72,"dscr":1.18,"ha":70,"crop":"Varkorn","years":12,"uc":690},
]

# Get current farmer data based on selected_app
def current_farmer():
    name = st.session_state.get("analyst_app") or st.session_state.get("bank_app")
    base = PIPELINE[0]  # Default: Erik
    if name:
        for p in PIPELINE:
            if p["name"] == name:
                base = p; break
    # Override with farmer's own form inputs if available
    result = dict(base)
    if st.session_state.get("farmer_crop"):
        result["crop"] = st.session_state.farmer_crop
    if st.session_state.get("farmer_ha"):
        result["ha"] = st.session_state.farmer_ha
    if st.session_state.get("farmer_years"):
        result["years"] = st.session_state.farmer_years
    if "farmer_insurance" in st.session_state:
        result["insurance"] = st.session_state.farmer_insurance
    return result

def current_financials():
    cf = current_farmer()
    scale = cf.get("ha", 85) / 85
    return [{**f, "rev":int(f["rev"]*scale), "opex":int(f["opex"]*scale),
             "ni":int(f["ni"]*scale), "ta":int(f["ta"]*scale), "tl":int(f["tl"]*scale),
             "ca":int(f["ca"]*scale), "cl":int(f["cl"]*scale),
             "ebitda":int(f["ebitda"]*scale), "cfo":int(f["cfo"]*scale)} for f in FIN]

# Shortcuts for current farmer/financials
def CF(): return current_farmer()
def CFIN(): return current_financials()

# ═══════════════ HELPERS ═══════════════
def ratios(fin, loans):
    if not fin: return {}
    f=fin[0]; rev=max(f.get("rev",1),1)
    ebitda=f.get("ebitda",f.get("ni",0)+f.get("int",0)+f.get("dep",0))
    ta=max(f.get("ta",1),1); tl=f.get("tl",0); ca=f.get("ca",0); cl=max(f.get("cl",1),1)
    eq=ta-tl; tds=sum(l.get("emi",0)*12 for l in loans); td=sum(l.get("out",0) for l in loans)
    return {"dti":round(td/rev,4),"dscr":round(ebitda/max(tds,1),2),"wc":ca-cl,"om":round((rev-f.get("opex",0))/rev,4),"ltv":round(td/ta,4),"ac":round(ta/max(td,1),2),"cr":round(ca/cl,2),"dte":round(tl/max(eq,1),4),"cfm":round(f.get("cfo",0)/rev,4),"icr":round(ebitda/max(f.get("int",1),1),2)}

def predict(fin, loans, farm):
    if not MODEL_OK: return None
    r=ratios(fin, loans)
    on_t=sum(l.get("on_time",0) for l in loans); due=max(sum(l.get("due",1) for l in loans),1)
    feats=np.array([[r.get("dti",0),r.get("dscr",1),r.get("wc",0)/100000,r.get("om",0),r.get("ltv",0),r.get("ac",1),r.get("cr",1),r.get("dte",0),r.get("cfm",0),r.get("icr",1),on_t/due,0.23,0.018,farm.get("ha",50),1 if farm.get("insurance") else 0]])
    m=bundle["models"]
    risk=float(m["credit_risk_classifier"].predict_proba(feats)[0,1])
    repay=float(m["repayment_regressor"].predict(feats)[0])
    cap=float(m["debt_capacity_regressor"].predict(feats)[0])
    lvl="Low" if risk<0.25 else "Medium" if risk<0.50 else "High"
    return {"risk":round(risk,4),"repay":round(repay,4),"cap":round(cap,2),"level":lvl}

# ═══════════════ CSS ═══════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
#MainMenu,footer,header{visibility:hidden}

/* ── Ambient Background ── */
.stApp{
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(180,120,40,0.08), transparent),
    radial-gradient(ellipse 60% 40% at 90% 80%, rgba(100,160,80,0.06), transparent),
    radial-gradient(ellipse 50% 30% at 10% 90%, rgba(60,120,180,0.05), transparent),
    #080c14 !important;
}

/* ── Animated grain overlay ── */
.stApp::before{
  content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  opacity:0.4;
}

/* ── Landing ── */
.landing{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:40vh;text-align:center;position:relative;z-index:1}
.landing h1{font-family:'Space Grotesk',sans-serif;font-size:3.5rem;font-weight:700;background:linear-gradient(135deg,#f7d774 0%,#e8962e 40%,#c45a1a 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.04em;margin:0;filter:drop-shadow(0 0 30px rgba(232,150,46,0.3))}
.landing .sub{color:#7a8a9e;font-size:1.15rem;margin:1rem 0 3rem 0}

.role-row{display:flex;gap:1.5rem;justify-content:center;position:relative;z-index:1}
.role-btn{
  background:linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));
  border:1px solid rgba(255,255,255,0.08);
  border-radius:20px;padding:1.5rem 2.5rem;cursor:pointer;
  transition:all 0.35s cubic-bezier(0.25,0.8,0.25,1.2);
  text-align:center;min-width:200px;
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
}
.role-btn:hover{
  background:linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03));
  border-color:rgba(240,192,96,0.5);
  transform:translateY(-6px) scale(1.02);
  box-shadow:0 24px 48px rgba(0,0,0,0.6),0 0 40px rgba(212,117,26,0.1);
}
.role-btn .icon{font-size:2.8rem;display:block;margin-bottom:0.5rem;transition:transform 0.35s}
.role-btn:hover .icon{transform:scale(1.15)}
.role-btn .name{font-family:'Space Grotesk',sans-serif;font-size:1.15rem;font-weight:700;color:#e8ecf1;display:block}
.role-btn .hint{font-size:0.75rem;color:#7a8a9e;margin-top:0.25rem;display:block}

/* ── Flow indicator ── */
.flow-bar{
  display:flex;align-items:center;justify-content:center;gap:1.5rem;
  padding:0.6rem 1rem;margin-bottom:1rem;
  background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));
  border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;font-size:0.82rem;color:#7a8a9e;
  backdrop-filter:blur(8px);
}
.flow-step{display:flex;align-items:center;gap:0.4rem;transition:all 0.3s}
.flow-step.current{
  color:#f0c060;font-weight:700;
  text-shadow:0 0 12px rgba(240,192,96,0.3);
}
.flow-arrow{color:#2a3040}

/* ── Product Banner ── */
.product-banner{
  background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));
  border:1px solid rgba(255,255,255,0.06);
  border-radius:16px;padding:1rem 1.5rem;margin-bottom:1.5rem;
  backdrop-filter:blur(12px);
  position:relative;overflow:hidden;
}
.product-banner::after{
  content:'';position:absolute;top:0;right:0;width:200px;height:100%;
  background:linear-gradient(90deg,transparent,rgba(240,192,96,0.03));
  pointer-events:none;
}
.product-banner .app-id{font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#5a6a7e;margin-bottom:0.5rem}
.product-banner .banner-row{display:flex;gap:2rem;align-items:center;flex-wrap:wrap;position:relative;z-index:1}
.banner-item .bl{font-size:0.6rem;color:#5a6a7e;text-transform:uppercase;letter-spacing:0.12em;font-weight:600}
.banner-item .bv{font-size:1rem;font-weight:700;color:#e8ecf1}

/* ── Timeline ── */
.timeline-step{
  border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;margin-bottom:0.5rem;overflow:hidden;
  background:linear-gradient(135deg,rgba(255,255,255,0.02),rgba(255,255,255,0.005));
  transition:border-color 0.3s,box-shadow 0.3s;
}
.timeline-step:hover{border-color:rgba(255,255,255,0.1);box-shadow:0 4px 20px rgba(0,0,0,0.3)}
.timeline-header{display:flex;align-items:center;gap:0.75rem;padding:0.85rem 1rem;cursor:pointer;transition:background 0.2s}
.timeline-header:hover{background:rgba(255,255,255,0.02)}
.timeline-num{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;border:2px solid #2a3040;color:#5a6a7e;flex-shrink:0;transition:all 0.3s}
.timeline-num.done{
  border-color:#34d399;background:rgba(16,185,129,0.15);color:#34d399;
  box-shadow:0 0 12px rgba(16,185,129,0.15);
}
.timeline-num.active{
  border-color:#f0c060;background:rgba(240,192,96,0.15);color:#f0c060;
  box-shadow:0 0 12px rgba(240,192,96,0.15);
  animation:pulse-ring 2s infinite;
}
@keyframes pulse-ring{
  0%,100%{box-shadow:0 0 8px rgba(240,192,96,0.15)}
  50%{box-shadow:0 0 20px rgba(240,192,96,0.3)}
}
.timeline-title{font-size:0.85rem;font-weight:600;color:#e8ecf1}
.timeline-status{font-size:0.7rem;margin-left:auto}
.timeline-body{padding:0 1rem 1rem 3.5rem}

/* ── Cards ── */
.card{
  background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));
  border:1px solid rgba(255,255,255,0.06);
  border-radius:16px;padding:1.25rem;
  backdrop-filter:blur(10px);
  transition:border-color 0.3s,box-shadow 0.3s,transform 0.3s;
}
.card:hover{
  border-color:rgba(255,255,255,0.12);
  box-shadow:0 8px 32px rgba(0,0,0,0.4);
}
.card-sm{
  background:linear-gradient(135deg,rgba(255,255,255,0.025),rgba(255,255,255,0.005));
  border:1px solid rgba(255,255,255,0.05);
  border-radius:12px;padding:0.75rem 1rem;margin:0.3rem 0;
  transition:all 0.25s;
}
.card-sm:hover{
  border-color:rgba(255,255,255,0.1);
  background:linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));
}

/* ── Metric ── */
.metric-row{display:flex;gap:0.75rem;flex-wrap:wrap}
.metric-item{
  background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));
  border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;padding:1rem 1.25rem;flex:1;min-width:130px;
  transition:all 0.3s;position:relative;overflow:hidden;
}
.metric-item::before{
  content:'';position:absolute;top:0;left:0;width:100%;height:2px;
  background:linear-gradient(90deg,transparent,rgba(240,192,96,0.3),transparent);
  opacity:0;transition:opacity 0.3s;
}
.metric-item:hover::before{opacity:1}
.metric-item .mv{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;color:#e8ecf1}
.metric-item .ml{font-size:0.6rem;color:#5a6a7e;text-transform:uppercase;letter-spacing:0.1em;font-weight:600}

/* ── Badge ── */
.badge{display:inline-block;padding:0.2rem 0.6rem;border-radius:6px;font-size:0.68rem;font-weight:600}
.badge-g{background:rgba(16,185,129,0.12);color:#34d399;border:1px solid rgba(16,185,129,0.25)}
.badge-y{background:rgba(245,158,11,0.12);color:#fbbf24;border:1px solid rgba(245,158,11,0.25)}
.badge-r{background:rgba(239,68,68,0.12);color:#f87171;border:1px solid rgba(239,68,68,0.25);animation:pulse-badge 3s infinite}
@keyframes pulse-badge{0%,100%{opacity:1}50%{opacity:0.75}}

/* ── Info / Warn ── */
.info{
  background:rgba(59,130,246,0.06);border-left:3px solid #60a5fa;
  padding:0.75rem 1rem;border-radius:0 10px 10px 0;color:#94a3b8;font-size:0.82rem;margin:0.75rem 0;
}
.warn{
  background:rgba(245,158,11,0.06);border-left:3px solid #fbbf24;
  padding:0.75rem 1rem;border-radius:0 10px 10px 0;color:#94a3b8;font-size:0.82rem;margin:0.75rem 0;
}
.sec{
  font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;
  background:linear-gradient(135deg,#f0c060,#d4751a);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  margin-bottom:0.5rem;
}

/* ── Buttons ── */
.stButton>button{
  border-radius:10px!important;font-weight:600!important;letter-spacing:0.02em!important;
  transition:all 0.25s cubic-bezier(0.25,0.8,0.25,1)!important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#e08820,#c45a1a)!important;border:none!important;color:#fff!important;
  box-shadow:0 2px 12px rgba(212,117,26,0.2)!important;
}
.stButton>button[kind="primary"]:hover{
  background:linear-gradient(135deg,#f0a040,#e08820)!important;
  box-shadow:0 6px 24px rgba(212,117,26,0.35)!important;
  transform:translateY(-1px)!important;
}
.stButton>button[kind="secondary"]{
  background:rgba(255,255,255,0.03)!important;
  border:1px solid rgba(255,255,255,0.08)!important;color:#c0c8d4!important;
}
.stButton>button[kind="secondary"]:hover{
  border-color:rgba(255,255,255,0.18)!important;
  background:rgba(255,255,255,0.06)!important;color:#e8ecf1!important;
}

/* ── Forms ── */
.stSelectbox>div>div,.stTextInput>div>div,.stTextArea>div>div{
  background:rgba(255,255,255,0.03)!important;
  border-color:rgba(255,255,255,0.08)!important;
  border-radius:10px!important;color:#e8ecf1!important;
}
.stSlider>div>div>div{background:linear-gradient(90deg,#d4751a,#f0c060)!important}
.stProgress>div>div{background:linear-gradient(90deg,#d4751a,#f0c060)!important;border-radius:6px!important}
[data-testid="stDataFrame"]{border-radius:14px!important;overflow:hidden!important}
.stRadio>div{flex-direction:row!important;gap:1rem!important}
hr{border-color:rgba(255,255,255,0.06)!important}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.06);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.12)}

/* ── Pipeline row hover ── */
.pipeline-row{transition:all 0.25s}
.pipeline-row:hover{background:rgba(255,255,255,0.02)}

/* ── Filter chip ── */
.filter-active{
  background:rgba(240,192,96,0.1)!important;
  border-color:rgba(240,192,96,0.3)!important;
}

/* ── Filter buttons - card-like ── */
button:has(div p) {
  padding: 0.7rem 0.5rem !important;
  min-height: 58px !important;
  font-weight: 700 !important;
  font-size: 0.82rem !important;
  border-radius: 12px !important;
  white-space: nowrap !important;
}

/* ── Responsive: Mobile ── */
@media (max-width: 768px) {
  /* Stack all horizontal blocks full-width */
  [data-testid="stHorizontalBlock"]{
    flex-wrap:wrap!important;gap:0.3rem!important;
    flex-direction:column!important;
  }
  [data-testid="stColumn"]{
    width:100%!important;max-width:100%!important;flex:1 1 100%!important;
  }

  /* Landing */
  .landing h1{font-size:2.2rem!important}
  .role-btn{min-width:unset!important;width:100%!important}

  /* Product banner */
  .product-banner .banner-row{gap:0.5rem!important}
  .banner-item .bv{font-size:0.82rem!important}

  /* Filter buttons */
  button:has(div p){min-height:44px!important;font-size:0.78rem!important;padding:0.5rem!important}

  /* Application list */
  .card{padding:0.75rem!important}
  .metric-item{min-width:80px!important;padding:0.6rem 0.8rem!important}
  .metric-item .mv{font-size:1.1rem!important}

  /* Timeline */
  .timeline-body{padding:0 0.5rem 0.75rem 2rem!important}
}

@media (max-width: 480px) {
  .landing h1{font-size:1.7rem!important}
  button:has(div p){font-size:0.72rem!important;min-height:40px!important}
}
</style>""",unsafe_allow_html=True)

# ═══════════════ STATE ═══════════════
for k,v in {
    "role":None,"farmer_step":1,"analyst_app":None,"bank_app":None,"farmer_submitted":False,
    "bank_decision":None,"memo_generated":False,"memo_sent":False,"scenario_result":None,
    "farmer_crop":None,"farmer_ha":None,"farmer_years":None,"farmer_insurance":True,"farmer_invest":None,
}.items():
    if k not in st.session_state: st.session_state[k]=v

# Step circle for wizard
STEPS_CSS = """<style>.step-circle{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;border:2px solid #333;color:#667085;flex-shrink:0}.step-circle.active{border-color:#f0c060;background:rgba(240,192,96,0.12);color:#f0c060}.step-circle.done{border-color:#34d399;background:rgba(16,185,129,0.12);color:#34d399}</style>"""
st.markdown(STEPS_CSS,unsafe_allow_html=True)

# ═══════════════ FLOW INDICATOR ═══════════════
def flow_indicator(role):
    roles = [
        ("👨‍🌾 Farmer","farmer"),
        ("🏢 Credit Analyst","analyst"),
        ("🏦 Bank Officer","bank"),
    ]
    html = '<div class="flow-bar">'
    for i,(label,key) in enumerate(roles):
        cls = "current" if key==role else ""
        html += f'<span class="flow-step {cls}">{label}</span>'
        if i<2: html += '<span class="flow-arrow">↓</span>'
    html += '</div>'
    st.markdown(html,unsafe_allow_html=True)

# ═══════════════ PRODUCT BANNER ═══════════════
def product_banner(pred, role_label):
    cf = current_farmer()
    rc = "#34d399" if pred and pred["level"]=="Low" else "#fbbf24" if pred and pred["level"]=="Medium" else "#f87171"
    rec = "Proceed" if pred and pred["level"]=="Low" else "Proceed with Conditions" if pred and pred["level"]=="Medium" else "Manual Review"

    dec = st.session_state.bank_decision
    if dec:
        status_color = "#34d399" if dec["decision"] == "Approve" else "#fbbf24" if "Conditions" in dec["decision"] else "#f87171"
        status_text = f"DECIDED: {dec['decision'].upper()}"
    else:
        status_color = "#34d399"
        status_text = "READY FOR ASSESSMENT"

    st.markdown(f"""
    <div class="product-banner">
        <div class="app-id">{cf.get('id',APP_ID)} · {cf['name']} · {cf.get('district','')}, {cf['region']} · {cf.get('ha',85)} ha {cf.get('crop','Hostvete')}</div>
        <div class="banner-row">
            <div class="banner-item"><div class="bl">Status</div><div class="bv" style="color:{status_color}">{status_text}</div></div>
            <div style="color:#333;">│</div>
            <div class="banner-item"><div class="bl">Evidence</div><div class="bv">94%</div></div>
            <div style="color:#333;">│</div>
            <div class="banner-item"><div class="bl">AI Confidence</div><div class="bv">91%</div></div>
            <div style="color:#333;">│</div>
            <div class="banner-item"><div class="bl">Recommendation</div><div class="bv" style="color:{rc}">{rec}</div></div>
            <div style="color:#333;">│</div>
            <div class="banner-item"><div class="bl">Last Updated</div><div class="bv" style="font-weight:400;">{datetime.now().strftime('%b %d, %H:%M')}</div></div>
        </div>
        <div style="margin-top:0.5rem;"><span style="color:#667085;font-size:0.68rem;">Viewing as:</span> <span style="color:#f0c060;font-weight:600;font-size:0.75rem;">{role_label}</span></div>
    </div>""",unsafe_allow_html=True)

# ═══════════════ TIMELINE ═══════════════
def timeline(pred, r, expanded_sections):
    """Render the 8-step application journey timeline."""
    steps = [
        (1, "Documents", "documents", "✅ Verified", True,
         lambda: st.markdown("✅ Bank Statements · ✅ Tax Returns · ✅ Land Registry · ✅ Loans · ⚠️ Machinery · ✅ Insurance\n\nReliability: **94%**")),
        (2, "Validation", "validation", "✅ Passed", True,
         lambda: st.markdown("All documents validated. Currency standardized to SEK. Area converted to hectares. No critical issues.")),
        (3, "Financial Analysis", "financials", "✅ Complete", True,
         lambda: financial_content(r, pred)),
        (4, "External Intelligence", "external", "✅ Live", True,
         lambda: st.markdown("🌦️ Weather: Normal (Skane)  ·  📉 Wheat: 2.48 kr/kg (-1.8%)  ·  🦠 Disease Risk: Low  ·  💶 EU CAP: 115,000 kr")),
        (5, "AI Assessment", "ai", "✅ Complete", True,
         lambda: ai_content(pred)),
        (6, "Scenario Simulation", "scenario", "⚡ Run", False,
         lambda: scenario_content(pred, r)),
        (7, "Decision Memo", "memo",
         "📤 Sent to Bank" if st.session_state.memo_sent else "✅ Generated" if st.session_state.memo_generated else "📝 Generate",
         st.session_state.memo_generated,
         lambda: memo_content(pred, r)),
        (8, "Final Decision", "decision",
         f"✅ {st.session_state.bank_decision['decision']}" if st.session_state.bank_decision else "⏳ Pending",
         bool(st.session_state.bank_decision),
         lambda: decision_content()),
    ]

    for num, title, key, status, done, render_fn in steps:
        num_cls = "done" if done else "active" if key in expanded_sections else ""
        with st.container():
            st.markdown(f"""
            <div class="timeline-step">
                <div class="timeline-header">
                    <div class="timeline-num {num_cls}">{'✓' if done else num}</div>
                    <div class="timeline-title">{title}</div>
                    <div class="timeline-status" style="color:{'#34d399' if done else '#667085'}">{status}</div>
                </div>
            </div>""",unsafe_allow_html=True)

        # Expand if requested
        if key in expanded_sections or (done and key in ["financials","ai"]):
            st.markdown(f'<div class="timeline-body">',unsafe_allow_html=True)
            render_fn()
            st.markdown('</div>',unsafe_allow_html=True)

def financial_content(r, pred):
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("DSCR", f"{r.get('dscr',0):.2f}x")
    with c2: st.metric("Debt-to-Income", f"{r.get('dti',0):.1%}")
    with c3: st.metric("Operating Margin", f"{r.get('om',0):.1%}")
    with c4: st.metric("Debt Capacity", f"{pred['cap']/1000:.0f}K kr" if pred else "N/A")

def ai_content(pred):
    if not pred: return
    rc = "#34d399" if pred["level"]=="Low" else "#fbbf24"
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Risk", f"{pred['risk']:.1%}")
    with c2: st.metric("Repayment Probability", f"{pred['repay']:.1%}")
    with c3: st.metric("Level", pred["level"])
    st.caption("Top drivers: DSCR · Debt Ratio · Cash Flow · Interest Coverage")

def scenario_content(pred, r):
    invest = st.radio("Buy Tractor Scenario", ["No change","Maybe - evaluate","Yes - simulate purchase"], horizontal=True, key="scn_radio")
    if "Yes" in invest:
        st.session_state.scenario_result = {"text":"Risk decreases by ~2% with tractor purchase. Improved productivity offsets additional debt.","delta":-0.02}
        st.success(st.session_state.scenario_result["text"])
    elif "Maybe" in invest:
        st.session_state.scenario_result = {"text":"Risk increases slightly (+1%) under conservative assumptions.","delta":0.01}
        st.warning(st.session_state.scenario_result["text"])
    elif st.session_state.scenario_result:
        st.info(st.session_state.scenario_result["text"])

def memo_content(pred, r):
    if st.session_state.memo_generated:
        # Show the persisted memo
        rc = "#34d399" if pred and pred["level"]=="Low" else "#fbbf24"
        rec = "PROCEED" if pred and pred["level"]=="Low" else "PROCEED WITH CONDITIONS" if pred and pred["level"]=="Medium" else "MANUAL REVIEW REQUIRED"
        st.success("✅ Decision Memo - Generated")
        cf = current_farmer()
        st.markdown(f"""<div class="card" style="text-align:left;line-height:1.8;">
        <div style="font-family:'JetBrains Mono',monospace;color:#667085;font-size:0.7rem;margin-bottom:0.75rem;">{cf.get('id',APP_ID)} · Generated {datetime.now().strftime('%b %d, %H:%M')}</div>
        <div class="sec">Applicant</div><strong style="color:#e8ecf1;font-size:1.05rem;">{cf['name']}</strong><br><span style="color:#94a3b8;font-size:0.82rem;">{cf.get('district','')}, {cf['region']} · {cf.get('ha',85)} ha {cf.get('crop','Hostvete')} · {cf.get('years',18)} years · UC {cf.get('uc',720)}</span>
        <div class="sec" style="margin-top:1rem;">Financial Summary</div>
        <table style="width:100%;font-size:0.82rem;color:#94a3b8;">
        <tr><td>Annual Revenue</td><td style="color:#e8ecf1;text-align:right;">{CFIN()[0]['rev']/1000:.0f}K kr</td></tr>
        <tr><td>DSCR</td><td style="color:#34d399;text-align:right;font-weight:600;">{r.get('dscr',0):.2f}x</td></tr>
        <tr><td>Debt-to-Income</td><td style="color:#fbbf24;text-align:right;">{r.get('dti',0):.1%}</td></tr>
        <tr><td>Operating Margin</td><td style="color:#e8ecf1;text-align:right;">{r.get('om',0):.1%}</td></tr>
        <tr><td>Existing Debt</td><td style="color:#e8ecf1;text-align:right;">{sum(l['out'] for l in LOANS)/1000:.0f}K kr</td></tr></table>
        <div class="sec" style="margin-top:1rem;">AI Assessment</div>
        <table style="width:100%;font-size:0.82rem;color:#94a3b8;">
        <tr><td>Risk</td><td style="color:{rc};text-align:right;font-weight:600;">{pred['risk']:.1%}</td></tr>
        <tr><td>Repayment</td><td style="color:#34d399;text-align:right;">{pred['repay']:.1%}</td></tr>
        <tr><td>Capacity</td><td style="color:#e8ecf1;text-align:right;">{pred['cap']/1000:.0f}K kr</td></tr></table>
        <div class="sec" style="margin-top:1rem;">Recommendation</div>
        <div style="font-size:1.1rem;font-weight:700;color:{rc};">{rec}</div>
        <span style="color:#94a3b8;font-size:0.82rem;">Standard terms with quarterly review. Monitor spring liquidity.</span></div>""",unsafe_allow_html=True)
        if not st.session_state.memo_sent:
            c1,c2 = st.columns(2)
            with c1:
                if st.button("📤 Send to Bank",type="primary",use_container_width=True):
                    st.session_state.memo_sent = True
                    # Update pipeline so everyone sees progress
                    cf = current_farmer()
                    for p in PIPELINE:
                        if p["name"] == cf["name"]:
                            p["status"] = "Sent to Bank"
                    st.success("Credit package sent to bank!"); st.rerun()
            with c2:
                if st.button("🔄 Regenerate",use_container_width=True):
                    st.session_state.memo_generated = False; st.rerun()
        else:
            st.markdown('<span class="badge badge-g">📤 Sent to Bank</span>',unsafe_allow_html=True)
        return

    if st.button("📝 Generate Decision Memo", type="primary"):
        with st.spinner("Preparing credit assessment memo..."): time.sleep(0.8)
        st.session_state.memo_generated = True
        st.rerun()

def decision_content():
    # If decision already made, show it
    if st.session_state.bank_decision:
        dec = st.session_state.bank_decision
        color = "#34d399" if dec["decision"]=="Approve" else "#fbbf24" if "Conditions" in dec["decision"] else "#f87171"
        st.markdown(f"""
        <div class="card" style="text-align:center;border-color:{color};">
            <div style="font-size:1.2rem;font-weight:800;color:{color};">✅ Decision Recorded</div>
            <div style="font-size:0.9rem;color:#e8ecf1;margin-top:0.5rem;"><strong>{dec['decision']}</strong></div>
            <div style="color:#94a3b8;font-size:0.8rem;margin-top:0.3rem;">{dec['notes']}</div>
            <div style="color:#667085;font-size:0.65rem;margin-top:0.5rem;">{dec['timestamp']}</div>
        </div>
        """,unsafe_allow_html=True)
        if st.button("🔄 Reset Decision",use_container_width=True):
            st.session_state.bank_decision = None; st.rerun()
        return

    d = st.radio("Decision",["Approve","Approve with Conditions","Reject"],horizontal=True,key="dec_radio")
    notes = ""
    can_submit = True

    if d == "Approve with Conditions":
        notes = st.text_area("Conditions (required)",placeholder="e.g., Additional collateral of 200,000 kr required within 90 days...",height=80)
        if not notes.strip():
            st.warning("⚠️ You must enter at least one condition before submitting.")
            can_submit = False
    elif d == "Reject":
        notes = st.text_area("Reason for rejection (required)",placeholder="e.g., DSCR below minimum threshold of 1.0x...",height=80)
        if not notes.strip():
            st.warning("⚠️ You must provide a reason for rejection.")
            can_submit = False
    else:
        notes = st.text_area("Internal notes (optional)",placeholder="Loan officer notes...",height=60)

    if can_submit:
        if st.button("✅ Submit Decision",type="primary"):
            from datetime import datetime
            st.session_state.bank_decision = {
                "decision": d,
                "notes": notes if notes else "No additional notes.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            # Update pipeline so everyone sees the outcome
            cf = current_farmer()
            new_status = "Approved" if d=="Approve" else ("Approved w/ Cond" if "Conditions" in d else "Rejected")
            for p in PIPELINE:
                if p["name"] == cf["name"]:
                    p["status"] = new_status
            st.success(f"Decision recorded: **{d}**")
            st.rerun()
    else:
        st.button("✅ Submit Decision",type="primary",disabled=True)

# ═══════════════ LANDING ═══════════════
def landing():
    st.markdown('<div class="landing"><h1>AgriSense AI</h1><p class="sub">Explainable Decision Support for Agricultural Finance</p><p style="color:#667085;font-size:0.85rem;">Choose your perspective - same application, different view.</p><div class="role-row">',unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,1,1])
    with c1:
        st.markdown('<div class="role-btn"><span class="icon">👨‍🌾</span><span class="name">Farmer</span><span class="hint">My application</span></div>',unsafe_allow_html=True)
        if st.button("Farmer View",key="lf",use_container_width=True,type="primary"): st.session_state.role="farmer";st.rerun()
    with c2:
        st.markdown('<div class="role-btn"><span class="icon">🏢</span><span class="name">Credit Analyst</span><span class="hint">Review & prepare</span></div>',unsafe_allow_html=True)
        if st.button("Analyst View",key="la",use_container_width=True,type="primary"): st.session_state.role="analyst";st.rerun()
    with c3:
        st.markdown('<div class="role-btn"><span class="icon">🏦</span><span class="name">Bank Officer</span><span class="hint">Review & decide</span></div>',unsafe_allow_html=True)
        if st.button("Bank View",key="lb",use_container_width=True,type="primary"): st.session_state.role="bank";st.rerun()
    st.markdown('</div></div>',unsafe_allow_html=True)
    st.divider()
    st.caption("2,500 farmers · 11 regions · v1.1.0 · 5 free APIs · Advisory only")

# ═══════════════ TOP BAR ═══════════════
def top_bar(role, label):
    c1,c2,c3 = st.columns([1,2,1])
    with c1:
        st.markdown('<span style="font-weight:900;background:linear-gradient(135deg,#f0c060,#d4751a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:1.1rem;">🌱 AgriSense AI</span>',unsafe_allow_html=True)
    with c3:
        if st.button("← Exit",key="exit"): st.session_state.role=None;st.rerun()
    flow_indicator(role)
    pred = predict(CFIN(), LOANS, CF()); r = ratios(CFIN(), LOANS)
    product_banner(pred, label)

# ═══════════════ 👨‍🌾 FARMER ═══════════════
def farmer_view():
    if not st.session_state.farmer_submitted:
        farmer_wizard()
    else:
        farmer_dashboard()

def farmer_wizard():
    step = st.session_state.farmer_step

    # Step indicator
    steps = ["Welcome","Documents","Farm Details","Analysis","Results"]
    cols = st.columns(5)
    for i,(c,label) in enumerate(zip(cols,steps)):
        with c:
            cls = "done" if i+1 < step else "active" if i+1 == step else ""
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;"><div class="step-circle {cls}">{i+1}</div><span style="font-size:0.78rem;color:#667085;font-weight:{"600" if i+1<=step else "400"}">{label}</span></div>',unsafe_allow_html=True)
    st.divider()

    if step == 1:
        cf = current_farmer()
        st.markdown(f"## 👋 Welcome, {cf['name']}")
        st.markdown("Let's prepare your financing application.")
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Farm", f"{cf.get('ha',85)} ha")
        with c2: st.metric("Experience", f"{cf.get('years',18)} years")
        with c3: st.metric("Region", f"{cf.get('district','Lund')}, {cf['region']}")
        # Show machinery if set
        mach = st.session_state.get('farmer_machinery')
        if mach:
            st.caption(f"🚜 Machinery: {', '.join(mach)}")
        inv = st.session_state.get('farmer_invest')
        if inv and inv != "No plans":
            st.caption(f"📋 Planning to invest: {inv}")
        st.divider()
        if st.button("Start →",type="primary",use_container_width=True): st.session_state.farmer_step=2;st.rerun()

    elif step == 2:
        st.markdown("## 📄 Documents")
        st.caption("We need these to assess your application.")
        st.checkbox("Use demo documents (Erik Johansson)",True,disabled=True)
        for d in ["Bank Statement (2024)","Tax Returns (2022-24)","Land Registry","Existing Loans","Machinery Inventory","Crop Insurance"]:
            st.markdown(f'<div class="card-sm">✅ <strong style="color:#e8ecf1">{d}</strong> <small style="color:#667085">- Uploaded</small></div>',unsafe_allow_html=True)
        st.divider()
        c1,c2 = st.columns(2)
        with c1:
            if st.button("← Back",use_container_width=True): st.session_state.farmer_step=1;st.rerun()
        with c2:
            if st.button("Continue →",type="primary",use_container_width=True): st.session_state.farmer_step=3;st.rerun()

    elif step == 3:
        st.markdown("## 🌾 Farm Details")
        c1,c2 = st.columns(2)
        with c1:
            crop = st.selectbox("Primary Crop",["Hostvete","Varvete","Varkorn","Havre","Hostraps"],index=0)
            ha = st.number_input("Farm Size (ha)",10,500,85)
            yrs = st.number_input("Years Farming",1,50,18)
        with c2:
            ins = st.checkbox("Crop Insurance",True)
            machinery = st.multiselect("Machinery",["Tractor","Harvester","Plow","Seeder","Sprayer"],["Tractor","Harvester","Plow"])
            invest = st.selectbox("Planning to invest in?",["Tractor","Harvester","Irrigation","Storage","No plans"],index=0)
        st.divider()
        c1,c2 = st.columns(2)
        with c1:
            if st.button("← Back ",use_container_width=True): st.session_state.farmer_step=2;st.rerun()
        with c2:
            if st.button("Analyze →",type="primary",use_container_width=True):
                # Save form values to session state so predictions use them
                st.session_state.farmer_crop = crop
                st.session_state.farmer_ha = ha
                st.session_state.farmer_years = yrs
                st.session_state.farmer_insurance = ins
                st.session_state.farmer_machinery = machinery
                st.session_state.farmer_invest = invest
                st.session_state.farmer_step=4;st.rerun()

    elif step == 4:
        st.markdown("## 🔍 Analyzing...")
        steps = ["Checking documents...","Extracting financial data...","Checking weather...","Running AI models...","Preparing report..."]
        prog = st.progress(0); stat = st.empty()
        for i,s in enumerate(steps):
            stat.markdown(f"### {s}"); prog.progress((i+1)/len(steps)); time.sleep(0.5)
        st.session_state.farmer_step=5;st.rerun()

    elif step == 5:
        st.markdown("## 📊 Results")
        pred = predict(CFIN(), LOANS, CF()); r = ratios(CFIN(), LOANS)
        c1,c2,c3 = st.columns(3)
        with c1:
            dscr = r.get("dscr",0); c = "#34d399" if dscr>=1.5 else "#fbbf24" if dscr>=1.0 else "#f87171"
            st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:2rem;color:{c}">{"🟢 Strong" if dscr>=1.5 else "🟡 Adequate" if dscr>=1.0 else "🔴 Weak"}</div><div style="color:#667085;font-size:0.7rem;">REPAYMENT CAPACITY</div></div>',unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:2rem;color:#34d399">🟢 High</div><div style="color:#667085;font-size:0.7rem;">REPAYMENT LIKELIHOOD</div></div>',unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:2rem;color:#34d399">🟢 Covered</div><div style="color:#667085;font-size:0.7rem;">INSURANCE</div></div>',unsafe_allow_html=True)
        st.divider()
        # Dynamic improvements based on actual ratios
        dscr_val = r.get("dscr", 0)
        dti_val = r.get("dti", 0)
        imp = []
        if dscr_val < 1.25:
            imp.append(("📉", "Improve debt coverage", f"DSCR of {dscr_val:.2f}x is below 1.25x. Reduce existing loans or increase EBITDA."))
        if dti_val > 0.40:
            imp.append(("💰", "Reduce debt-to-income", f"DTI of {dti_val:.1%} is above 40%. Pay down debt or increase revenue."))
        if not imp:
            imp.append(("✅", "Strong profile", "Your ratios are healthy. Maintain current trajectory."))
        # Always show invest tip if one is planned
        inv = st.session_state.get('farmer_invest')
        if inv and inv != "No plans":
            imp.append(("📋", f"Evaluate {inv} investment", "Use the scenario simulator to see how this purchase affects your risk."))
        for icon, title, desc in imp[:3]:
            st.markdown(f'<div class="card-sm"><strong style="color:#e8ecf1">{icon} {title}</strong><br><small style="color:#667085">{desc}</small></div>',unsafe_allow_html=True)
        st.divider()
        c1,c2 = st.columns(2)
        with c1:
            if st.button("← Edit",use_container_width=True): st.session_state.farmer_step=1;st.rerun()
        with c2:
            if st.button("📤 Submit to Credit Analyst",type="primary",use_container_width=True):
                st.session_state.farmer_submitted = True
                # Update pipeline status so analyst sees it
                cf = current_farmer()
                for p in PIPELINE:
                    if p["name"] == cf["name"]:
                        p["status"] = "Submitted"
                st.success("Submitted!"); st.balloons(); time.sleep(1); st.rerun()

def farmer_dashboard():
    pred = predict(CFIN(), LOANS, CF()); r = ratios(CFIN(), LOANS)
    st.markdown("## My Application")
    st.caption("Your application has been submitted. Track status below.")

    # Show progress: Submitted → Under Review → Sent to Bank → Decision
    dec = st.session_state.bank_decision
    memo_sent = st.session_state.memo_sent
    memo_gen = st.session_state.memo_generated

    if dec:
        color = "#34d399" if dec["decision"]=="Approve" else "#fbbf24" if "Conditions" in dec["decision"] else "#f87171"
        emoji = "✅" if dec["decision"]=="Approve" else "⚠️" if "Conditions" in dec["decision"] else "❌"
        badge_class = "badge badge-g" if dec["decision"]=="Approve" else "badge badge-y" if "Conditions" in dec["decision"] else "badge badge-r"
        st.markdown(f'<span class="{badge_class}" style="font-size:0.8rem;">{emoji} {dec["decision"].upper()}</span>',unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="margin-top:1rem;border-left:4px solid {color};">
            <div style="font-size:1.1rem;font-weight:700;color:{color};">Bank Decision: {dec['decision']}</div>
            <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem;">{dec['notes']}</div>
            <div style="color:#667085;font-size:0.65rem;margin-top:0.5rem;">Recorded: {dec['timestamp']}</div>
        </div>
        """,unsafe_allow_html=True)
    elif memo_sent:
        st.markdown('<span class="badge badge-y" style="font-size:0.8rem;">📤 Sent to Bank</span>',unsafe_allow_html=True)
        st.caption("Your application is with the bank officer for final decision.")
    elif memo_gen:
        st.markdown('<span class="badge badge-y" style="font-size:0.8rem;">📝 Under Review</span>',unsafe_allow_html=True)
        st.caption("A credit analyst has prepared your assessment.")
    else:
        st.markdown('<span class="badge badge-g" style="font-size:0.8rem;">📤 Submitted</span>',unsafe_allow_html=True)
        st.caption("A credit analyst is reviewing your application.")

    c1,c2,c3 = st.columns(3)
    with c1:
        dscr = r.get("dscr",0); c = "#34d399" if dscr>=1.5 else "#fbbf24" if dscr>=1.0 else "#f87171"
        st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:2rem;color:{c}">{"🟢 Strong" if dscr>=1.5 else "🟡 Adequate" if dscr>=1.0 else "🔴 Weak"}</div><div style="color:#667085;font-size:0.7rem;">REPAYMENT CAPACITY</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:2rem;color:#34d399">🟢 High</div><div style="color:#667085;font-size:0.7rem;">REPAYMENT LIKELIHOOD</div></div>',unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:2rem;color:#34d399">🟢 Covered</div><div style="color:#667085;font-size:0.7rem;">INSURANCE</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="sec" style="margin-top:1.5rem;">Improvements</div>',unsafe_allow_html=True)
    dscr_val = r.get("dscr", 0)
    dti_val = r.get("dti", 0)
    imp = []
    if dscr_val < 1.25:
        imp.append(("📉", "Improve debt coverage", f"DSCR of {dscr_val:.2f}x is below 1.25x. Reduce existing loans or increase EBITDA."))
    if dti_val > 0.40:
        imp.append(("💰", "Reduce debt-to-income", f"DTI of {dti_val:.1%} is above 40%. Pay down debt or increase revenue."))
    if not imp:
        imp.append(("✅", "Strong profile", "Your ratios are healthy. Maintain current trajectory."))
    inv = st.session_state.get('farmer_invest')
    if inv and inv != "No plans":
        imp.append(("📋", f"Evaluate {inv} investment", "Use the scenario simulator to see how this purchase affects your risk."))
    for icon, title, desc in imp[:3]:
        st.markdown(f'<div class="card-sm"><strong style="color:#e8ecf1">{icon} {title}</strong><br><small style="color:#667085">{desc}</small></div>',unsafe_allow_html=True)

    st.markdown('<div class="sec" style="margin-top:1.5rem;">Investment Simulator</div>',unsafe_allow_html=True)
    invest = st.radio("Planning to invest in a tractor?",["Not now","Maybe next year","Yes, soon"],horizontal=True,key="fd_invest")
    if "Yes" in invest: st.success("Likely improves productivity. Risk impact: minimal.")
    elif "Maybe" in invest: st.info("Build cash reserves first, then apply with stronger numbers.")
    else: st.info("Your profile is solid without additional debt.")

    st.divider()
    # Only show this if no decision yet
    if not st.session_state.bank_decision:
        st.info("📤 Your application is being processed. You'll be notified when the bank reviews it.")
    else:
        st.success("Decision received! View the details above.")

# ═══════════════ 🏢 CREDIT ANALYST ═══════════════
def analyst_view():
    if st.session_state.analyst_app is None:
        analyst_pipeline()
    else:
        analyst_workspace()

def analyst_pipeline():
    st.markdown("## Applications")
    st.caption("Click a status to filter - then open an application to begin review.")

    ready = sum(1 for p in PIPELINE if p["status"]=="Ready")
    pending = sum(1 for p in PIPELINE if "Pending" in p["status"])
    review = sum(1 for p in PIPELINE if "Needs" in p["status"])
    submitted = sum(1 for p in PIPELINE if "Submitted" in p["status"])
    in_progress = sum(1 for p in PIPELINE if p["status"]=="In Progress")
    rejected = sum(1 for p in PIPELINE if p["status"]=="Rejected")
    total = len(PIPELINE)

    if "analyst_filter" not in st.session_state: st.session_state.analyst_filter = "Ready"
    af = st.session_state.analyst_filter

    # Colorful filter cards - emoji + label baked into button text
    filters = [
        ("Ready", ready, "🟢"),
        ("Pending Docs", pending, "🟡"),
        ("Needs Review", review, "🔴"),
        ("In Progress", in_progress, "🔵"),
        ("Submitted", submitted, "🟣"),
        ("All", total, "⚪"),
    ]

    fcols = st.columns(6)
    for i, (label, count, emoji) in enumerate(filters):
        with fcols[i]:
            active = af == label
            if st.button(f"{emoji}\n{count}  {label}", key=f"af_{label}", use_container_width=True,
                        type=("primary" if active else "secondary")):
                st.session_state.analyst_filter = label; st.rerun()

    st.divider()

    if af == "All": filtered = PIPELINE
    else: filtered = [p for p in PIPELINE if p["status"] == af]

    if not filtered:
        st.info(f"No applications with status: {af}")
        return

    # Update pipeline statuses from session state
    dec = st.session_state.bank_decision
    memo_sent = st.session_state.memo_sent
    if dec:
        new_status = "Approved" if dec["decision"]=="Approve" else ("Approved w/ Cond" if "Conditions" in dec["decision"] else "Rejected")
        for p in PIPELINE:
            if p["name"] == st.session_state.analyst_app:
                p["status"] = new_status
    elif memo_sent:
        for p in PIPELINE:
            if p["name"] == st.session_state.analyst_app:
                p["status"] = "Sent to Bank"

    for p in filtered:
        status = p['status']
        sc = "#34d399" if status in ("Ready","Submitted","Approved") else "#fbbf24" if "Pending" in status or "Sent" in status or "Cond" in status else "#f87171" if "Needs" in status or status=="Rejected" else "#60a5fa"
        badge = "g" if status in ("Ready","Submitted","Approved") else "y" if "Pending" in status or "Sent" in status or "Cond" in status else "r" if "Needs" in status or status=="Rejected" else "g"
        c1,c2,c3,c4,c5 = st.columns([2.5,1.5,1,1,1])
        with c1: st.markdown(f"**{p['name']}**  \n<small style='color:#667085'>{p.get('district','')}, {p['region']}</small>",unsafe_allow_html=True)
        with c2: st.markdown(f"<span class='badge badge-{badge}'>{status}</span>",unsafe_allow_html=True)
        with c3: st.markdown(f"<span style='color:#e8ecf1;font-size:0.85rem;font-weight:600;'>{p['score']}%</span>",unsafe_allow_html=True)
        with c4: st.markdown(f"<span style='color:#667085;font-size:0.8rem;'>DSCR {p['dscr']}</span>",unsafe_allow_html=True)
        with c5:
            if st.button("Open →",key=f"open_{p['name']}"): st.session_state.analyst_app=p['name'];st.rerun()

def analyst_workspace():
    if st.button("← Back to Pipeline"): st.session_state.analyst_app=None;st.rerun()
    pred = predict(CFIN(), LOANS, CF()); r = ratios(CFIN(), LOANS)

    st.markdown(f"## 📋 {st.session_state.analyst_app}")
    # Show full timeline
    timeline(pred, r, {"financials","ai","scenario","memo"})

# ═══════════════ 🏦 BANK ═══════════════
def bank_view():
    if st.session_state.bank_app is None:
        bank_pipeline()
    else:
        bank_workspace()

def bank_pipeline():
    st.markdown("## Applications")
    st.caption("Click a status to filter the list below.")

    total = len(PIPELINE)
    ready = sum(1 for p in PIPELINE if p["status"]=="Ready")
    submitted = sum(1 for p in PIPELINE if p["status"]=="Submitted")
    in_progress = sum(1 for p in PIPELINE if p["status"]=="In Progress")
    rejected = sum(1 for p in PIPELINE if p["status"]=="Rejected")
    needs_review = sum(1 for p in PIPELINE if p["status"]=="Needs Review")
    pending = sum(1 for p in PIPELINE if p["status"]=="Pending Docs")

    if "bank_filter" not in st.session_state: st.session_state.bank_filter = "Awaiting"
    active_filter = st.session_state.bank_filter

    # Colorful filter cards - emoji + label baked into button text
    filters = [
        ("Awaiting", ready+submitted, "🔵"),
        ("In Progress", in_progress+needs_review+pending, "🟡"),
        ("Rejected", rejected, "🔴"),
        ("Submitted", submitted, "🟢"),
        ("Needs Review", needs_review, "🟠"),
        ("All", total, "⚪"),
    ]

    fcols = st.columns(6)
    for i, (label, count, emoji) in enumerate(filters):
        with fcols[i]:
            active = active_filter == label
            if st.button(f"{emoji}\n{count}  {label}", key=f"filt_{label}", use_container_width=True,
                        type=("primary" if active else "secondary")):
                st.session_state.bank_filter = label; st.rerun()

    st.divider()

    # Filter pipeline
    if active_filter == "Awaiting":
        filtered = [p for p in PIPELINE if p["status"] in ("Ready","Submitted")]
    elif active_filter == "All":
        filtered = PIPELINE
    else:
        filtered = [p for p in PIPELINE if p["status"] == active_filter]

    if not filtered:
        st.info(f"No applications with status: {active_filter}")
        return

    for p in filtered:
        sc = "#34d399" if p["status"] in ("Ready","Submitted") else "#fbbf24" if p["status"] in ("Pending Docs","In Progress") else "#f87171"
        c1,c2,c3,c4,c5 = st.columns([2.5,1.5,1,1,1])
        with c1: st.markdown(f"**{p['name']}**  \n<small style='color:#667085'>{p.get('district','')}, {p['region']}</small>",unsafe_allow_html=True)
        with c2: st.markdown(f"<span class='badge badge-{'g' if p['status'] in ('Ready','Submitted') else 'y' if p['status'] in ('Pending Docs','In Progress') else 'r'}'>{p['status']}</span>",unsafe_allow_html=True)
        with c3: st.markdown(f"<span style='color:#e8ecf1;font-size:0.85rem;font-weight:600;'>{p['score']}%</span>",unsafe_allow_html=True)
        with c4: st.markdown(f"<span style='color:#667085;font-size:0.8rem;'>DSCR {p['dscr']}</span>",unsafe_allow_html=True)
        with c5:
            if st.button("Review →",key=f"bank_open_{p['name']}"): st.session_state.bank_app=p['name'];st.rerun()

def bank_workspace():
    if st.button("← Back to Applications"): st.session_state.bank_app=None;st.rerun()
    pred = predict(CFIN(), LOANS, CF()); r = ratios(CFIN(), LOANS)
    st.markdown(f"## ⚖️ {st.session_state.bank_app}")

    # Full timeline with all sections expandable, including decision
    timeline(pred, r, {"financials","ai","scenario","memo","decision"})
    st.divider()
    st.markdown('<div class="warn">⚠️ <strong>Advisory Only:</strong> The AI recommendation is decision support. Final authority rests with the human loan officer per institutional credit policy.</div>',unsafe_allow_html=True)

# ═══════════════ MAIN ═══════════════
if st.session_state.role is None:
    landing()
else:
    role_labels = {"farmer":"Farmer","analyst":"Credit Analyst","bank":"Bank Officer"}
    label = role_labels[st.session_state.role]
    top_bar(st.session_state.role, label)

    if st.session_state.role == "farmer":
        farmer_view()
    elif st.session_state.role == "analyst":
        analyst_view()
    elif st.session_state.role == "bank":
        bank_view()

st.divider()
st.caption("🌱 AgriSense AI · Swedish Demo · Advisory Only · Final decisions made by qualified humans")
