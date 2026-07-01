# AgriSense AI — Architecture Overview

> View on [GitHub](https://github.com/Uday-Kiran-01/AgriSense/blob/main/docs/architecture.md) for live Mermaid diagrams.  
> Export to PDF/PNG: copy any diagram block into [mermaid.live](https://mermaid.live)

---

## System Architecture

```mermaid
graph TB
    subgraph Users["👥 Users"]
        Farmer["👨‍🌾 Farmer<br/>5-step wizard"]
        Analyst["🏢 Credit Analyst<br/>Pipeline review"]
        Bank["🏦 Bank Officer<br/>Final decision"]
    end

    subgraph Frontend["🖥️ Streamlit Frontend"]
        UI["Streamlit App<br/>Port 8501<br/>HF Spaces"]
    end

    subgraph Backend["⚙️ FastAPI Backend :8000"]
        subgraph Routers["Routes (34 endpoints)"]
            FR["farmers.py"]
            AR["analysis.py"]
            MR["ml.py"]
        end

        subgraph Services["Services (16)"]
            FA["financial_analysis"]
            ML["ml_service RFx3"]
            SC["scenario_analysis"]
            LQ["liquidity"]
            PB["peer_benchmark"]
            DR["decision_readiness"]
            ED["external_data"]
            SH["shap_explainer"]
            GM["gemini_service"]
            EV["evaluation"]
            PP["preprocessing"]
            ES["environmental_score"]
        end

        subgraph Data["Data Layer"]
            DB[("SQLite WAL<br/>9 models")]
            ORM["SQLAlchemy ORM"]
        end
    end

    subgraph External["🌐 External APIs"]
        SMHI["SMHI Weather"]
        EU["EU Agri-Food"]
        FAO["FAOSTAT"]
        ESTAT["Eurostat"]
    end

    Farmer --> UI
    Analyst --> UI
    Bank --> UI
    UI --> Routers
    Routers --> Services
    Services --> ORM
    ORM --> DB
    ED --> SMHI
    ED --> EU
    ED --> FAO
    ED --> ESTAT
    ML --> SH
    SH --> GM
```

---

## Data Flow

```mermaid
flowchart LR
    A["📄 Docs"] --> B["✅ Validate"]
    B --> C["🧹 Clean"]
    C --> D["📐 Ratios<br/>DSCR DTI LTV"]
    D --> E["🔢 Features<br/>15 engineered"]
    E --> F["🌲 RF Model<br/>Risk+Repay+Capacity"]
    F --> G["📊 Risk Score"]
    G --> H["🔍 SHAP"]
    H --> I["📝 Memo<br/>Gemini AI"]
    I --> J["👤 Human Decision"]

    K["🌦️ Weather<br/>SMHI"] --> E
    L["📉 Commodity<br/>EU Agri-Food"] --> E
```

---

## Deployment

```mermaid
flowchart TB
    subgraph Local["💻 Local"]
        L1["streamlit run"]
        L2["uvicorn main"]
    end
    subgraph Docker["🐳 Docker"]
        D1["docker-compose up"]
        D2["FastAPI :8000"]
        D3["Streamlit :8501"]
    end
    subgraph Cloud["☁️ Cloud"]
        C1["HF Spaces"]
        C2["GitHub"]
    end
    Local --> Docker --> Cloud
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Streamlit 1.36 | Rapid prototyping, Python-native |
| Backend | FastAPI 3.11 | Async, OpenAPI, API-first |
| ML | scikit-learn RF × 3 | Explainable, tabular data |
| Explainability | SHAP + Gemini AI | Per-prediction + plain language |
| Database | SQLite WAL + SQLAlchemy | Simple, replaceable |
| Container | Docker compose | Reproducible |
| Deploy | HF Spaces + GitHub | Free, auto-rebuild |
| APIs | SMHI, EU, FAOSTAT, Eurostat | Real Swedish/EU data |
