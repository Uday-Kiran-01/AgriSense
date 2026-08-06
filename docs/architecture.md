# AgriSense AI - Architecture Overview

> View on [GitHub](https://github.com/Uday-Kiran-01/AgriSense) for live Mermaid diagrams.  
> Export to PNG: copy any diagram into [mermaid.live](https://mermaid.live)

---

## System Architecture (HF Spaces Deployment)

```mermaid
graph TB
    subgraph Users["👥 Users"]
        Farmer["👨‍🌾 Farmer<br/>5-step wizard"]
        Analyst["🏢 Credit Analyst<br/>Pipeline review"]
        Bank["🏦 Bank Officer<br/>Final decision"]
    end

    subgraph Frontend["🖥️ Standalone Streamlit App"]
        UI["app.py<br/>~1400 lines<br/>Single-file"]
        CSS["Dark theme<br/>Responsive"]
        Tabs["Tab-based timeline<br/>7 tabs (analyst)<br/>8 tabs (bank)"]
    end

    subgraph ML["🌲 Embedded ML"]
        RF["Random Forest x3<br/>Credit Risk · Repayment · Debt Capacity"]
        FE["15 engineered features<br/>10 financial ratios"]
    end

    subgraph Storage["💾 Data Layer"]
        SQLite[("SQLite<br/>agrisense_farmers.db<br/>Custom farmers persist")]
        SS["session_state<br/>Status overrides<br/>Farmer profiles"]
        Bundle["agrisense_model_bundle.pkl<br/>9.7 MB joblib"]
    end

    subgraph Future["🔮 Backend (future production)"]
        FastAPI["FastAPI"]
        SHAP["SHAP explainability"]
        Gemini["Gemini AI summaries"]
        APIs["SMHI · EU · FAO APIs"]
    end

    Farmer --> UI
    Analyst --> UI
    Bank --> UI
    UI --> ML
    UI --> Storage
    RF --> FE
    Future -.-> ML
```

---

## Data Flow

```mermaid
flowchart LR
    A["📄 Farmer Input<br/>Crop · ha · Years · Insurance"] --> B["💰 current_financials()<br/>Scaled by ha & crop multiplier"]
    B --> C["📐 ratios()<br/>DSCR · DTI · OM · LTV<br/>CR · ICR · D/E · CFM · WC · AC"]
    C --> D["🔢 predict()<br/>15 features → RF x3"]
    D --> E["📊 Risk % · Repay % · Capacity kr"]
    E --> F["📋 Memo<br/>Computed from actual ratios"]
    F --> G["👤 Bank Decision"]
```

---

## Session State Architecture

```mermaid
flowchart TB
    subgraph State["st.session_state"]
        Pipeline["pipeline_overrides<br/>Status per farmer"]
        Profiles["farmer_profiles<br/>Form inputs per farmer"]
        User["farmer_user<br/>Current logged-in farmer"]
        Role["role · analyst_app · bank_app"]
        Workflow["memo_generated · memo_sent · bank_decision"]
    end

    subgraph Functions["Key Functions"]
        GP["get_pipeline()<br/>Merge overrides"]
        SF["save_farmer_profile()<br/>Persist farmer inputs"]
        CF["current_farmer()<br/>Apply profiles for all roles"]
    end

    State --> Functions
```

---

## Deployment

```mermaid
flowchart TB
    subgraph Dev["💻 Development"]
        Code["git push origin master"]
    end
    subgraph CI["⚙️ GitHub Actions"]
        Action["deploy.yml<br/>on: push to master"]
        Checkout["Checkout code"]
        Upload["Upload to HF Spaces"]
    end
    subgraph Cloud["☁️ Cloud"]
        C1["HF Spaces<br/>SuperNitro/Agri-Sense"]
        C2["GitHub<br/>Uday-Kiran-01/AgriSense"]
    end
    subgraph Files["📦 Deployed Files"]
        F1["app.py"]
        F2["config.toml"]
        F3["requirements.txt"]
    end
    Code --> Action
    Action --> Checkout --> Upload --> C1
    C2 --> Code
    Files --> C1
```

**CI/CD:** Every `git push` to master triggers a GitHub Actions workflow that auto-deploys `app.py`, `.streamlit/config.toml`, and `requirements.txt` to HF Spaces. The model bundle (`agrisense_model_bundle.pkl`) is stored directly on HF Spaces since it rarely changes. Deploy time: ~30 seconds.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Streamlit 1.36 | Rapid prototyping, Python-native, single-file deploy |
| ML | scikit-learn RF x 3 | Explainable, tabular data, joblib serialized |
| Features | 15 engineered + 10 financial ratios | Transparent, auditable formulas |
| Storage | SQLite (built-in) | Zero-config, custom farmers persist across restarts |
| State | st.session_state | Pipeline overrides, farmer profiles survive reruns |
| Deploy | HF Spaces + GitHub | Free, auto-rebuild, no backend needed |
| Backend (future) | FastAPI + SHAP + Gemini | For production: explainability, APIs, auth |

---

## What the Demo App Actually Computes

| Component | Real or Demo | Details |
|-----------|-------------|---------|
| 10 financial ratios | **Real** | Standard formulas (DSCR=EBITDA/TDS, DTI=debt/revenue, etc.) |
| ML predictions | **Real** | Random Forest x3 on 15 features via joblib |
| Feature scaling | **Real** | ha_scale + crop_multiplier from farmer input |
| Scenario simulation | **Real** | Re-runs predict() with modified drought/price params |
| Pipeline status flow | **Real** | Draft → Submitted → In Review → Sent to Bank → Approved/Rejected |
| Custom farmer registration | **Real** | SQLite persistence, auto-login after registration |
| External intelligence | **Demo** | Template-based weather/prices, not live APIs |
| Farmer data (8 built-in) | **Demo** | Synthetic Swedish farmers, GDPR-safe |

