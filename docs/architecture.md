# AgriSense AI — Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        USERS & INTERFACES                          │
│                                                                    │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐   │
│  │   👨‍🌾 Farmer   │   │  🏢 Credit Analyst │   │  🏦 Bank Officer  │   │
│  │  5-step wizard│   │  Pipeline review │   │  Final decision  │   │
│  │  My farm, my  │   │  Filter, analyze,│   │  Approve/Condition│  │
│  │  application  │   │  generate memo   │   │  /Reject          │   │
│  └──────┬───────┘   └────────┬─────────┘   └────────┬─────────┘   │
│         │                    │                      │              │
│         └────────────────────┼──────────────────────┘              │
│                              │                                     │
│                   Streamlit (port 8501)                            │
│                   HuggingFace Spaces                               │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
                               │ HTTP/REST
                               │
┌──────────────────────────────┼─────────────────────────────────────┐
│                     FASTAPI BACKEND (port 8000)                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        ROUTERS                               │   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐   │   │
│  │  │  farmers.py  │  │   analysis.py    │  │    ml.py     │   │   │
│  │  │  10 routes   │  │    20 routes     │  │  4 routes    │   │   │
│  │  │  CRUD + data │  │  Predict, SHAP,  │  │  Evaluate,   │   │   │
│  │  │  + external  │  │  Scenarios, Memos│  │  Retrain     │   │   │
│  │  └──────────────┘  └──────────────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                       SERVICES (16)                           │   │
│  │                                                               │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐       │   │
│  │  │ financial   │ │ ml_service   │ │ scenario         │       │   │
│  │  │ _analysis   │ │ RF × 3       │ │ _analysis        │       │   │
│  │  │ DSCR, DTI.. │ │ Train+Predict│ │ What-if simulator│       │   │
│  │  └─────────────┘ └──────────────┘ └──────────────────┘       │   │
│  │                                                               │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐       │   │
│  │  │ liquidity   │ │ peer_bench   │ │ decision         │       │   │
│  │  │ Seasonal CF │ │ Percentile   │ │ _readiness       │       │   │
│  │  │ Stress test │ │ comparisons  │ │ Evidence quality │       │   │
│  │  └─────────────┘ └──────────────┘ └──────────────────┘       │   │
│  │                                                               │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐       │   │
│  │  │ external    │ │ shap         │ │ gemini           │       │   │
│  │  │ _data       │ │ _explainer   │ │ _service         │       │   │
│  │  │ SMHI, EU... │ │ Per-predict  │ │ Decision memos   │       │   │
│  │  └─────────────┘ └──────────────┘ └──────────────────┘       │   │
│  │                                                               │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐       │   │
│  │  │ evaluation  │ │ preprocessing│ │ environmental    │       │   │
│  │  │ 1K unseen   │ │ Validation   │ │ _score           │       │   │
│  │  │ + metrics   │ │ + Cleaning   │ │ Drought + price  │       │   │
│  │  └─────────────┘ └──────────────┘ └──────────────────┘       │   │
│  │                                                               │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐       │   │
│  │  │ model_      │ │ feature_      │ │ synthetic        │       │   │
│  │  │ benchmark   │ │ engineering   │ │ _generator       │       │   │
│  │  │ 5-model cmp │ │ Train/Test/   │ │ 2500 farmers     │       │   │
│  │  └─────────────┘ │ GridSearch    │ └──────────────────┘       │   │
│  │                  └──────────────┘                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     DATA LAYER                                │   │
│  │  ┌──────────────────────┐  ┌─────────────────────────────┐   │   │
│  │  │  SQLAlchemy ORM      │  │  External APIs              │   │   │
│  │  │  9 models, WAL mode  │  │  SMHI · EU Agri-Food        │   │   │
│  │  │  SQLite -> PostgreSQL│  │  FAOSTAT · Eurostat         │   │   │
│  │  └──────────────────────┘  └─────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Deployment

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Local Dev      │     │   Docker          │     │   Cloud          │
│                  │     │                   │     │                  │
│  streamlit run   │     │  docker-compose   │     │  HuggingFace     │
│  uvicorn main    │     │  FastAPI :8000    │     │  Spaces          │
│                  │     │  Streamlit :8501  │     │  (Streamlit SDK) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Data Flow

```
Documents ──> Validation ──> Cleaning ──> Ratios ──> Features ──> RF Model ──> Risk Score
                                                          │
External APIs ──> Weather/Commodity ─────────────────────┘
                                                          │
                                                          ▼
                                                    SHAP Explanation
                                                          │
                                                          ▼
                                                    Decision Memo
                                                          │
                                                          ▼
                                                    Human Decision
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.36 |
| Backend | FastAPI (Python 3.11) |
| ML | scikit-learn Random Forest × 3 |
| Explainability | SHAP + Gemini AI |
| Database | SQLite (WAL) + SQLAlchemy ORM |
| Container | Docker + docker-compose |
| Deployment | HuggingFace Spaces + GitHub |
| External APIs | SMHI, EU Agri-Food, FAOSTAT, Eurostat |
