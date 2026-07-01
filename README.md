# 🌱 AgriSense AI

**Explainable Decision Support for Agricultural Lending**

Live demo: [huggingface.co/spaces/SuperNitro/Agri-Sense](https://huggingface.co/spaces/SuperNitro/Agri-Sense)

---

AgriSense AI combines financial, operational, and environmental data into a transparent lending workflow. It never approves loans — it prepares evidence for humans who do.

> 🇸🇪 Swedish demo · Synthetic data · SEK currency · GDPR compliant · 2,500 farmers · 11 regions

---

## What It Does

| Role | Workflow |
|------|----------|
| 👨‍🌾 **Farmer** | 5-step wizard: Documents → Farm Details → Analysis → Results → Submit |
| 🏢 **Credit Analyst** | Pipeline with filter cards, financial analysis, SHAP explanations, decision memo generation |
| 🏦 **Bank Officer** | Review workspace with recommendation, scenario simulation, final approve/condition/reject |

---

## Architecture

```
Users → Streamlit → FastAPI → Routers (3) → Services (16) → SQLite
                                    ↓
                    External APIs (SMHI · EU Agri-Food · FAOSTAT · Eurostat)
```

- **3 routers:** farmers, analysis, ML ops (34 endpoints)
- **16 services:** financial analysis, ML (RF × 3), scenarios, liquidity, peer benchmarking, SHAP, Gemini memos, evaluation, preprocessing, environmental scoring
- **9 SQLAlchemy models:** farmer, loan, financial, operational, prediction, scenario, memo, document, external

---

## ML Approach

**Random Forest × 3** — credit risk classifier, repayment regressor, debt capacity regressor.

| Principle | Implementation |
|-----------|---------------|
| Explainability over complexity | SHAP per-prediction + deterministic financial ratios |
| Honest evaluation | 1,000 unseen farmers, 5 stress scenarios, frozen model |
| Human-in-the-loop | AI prepares evidence — humans decide |

**Evaluation (1,000 unseen farmers, shifted distributions):**

| Metric | Value |
|--------|-------|
| Accuracy | 80.1% |
| Precision | 99.4% |
| Recall | 70.9% |
| F1 | 82.8% |
| ROC-AUC | 90.0% |

**5 stress scenarios (500 farmers each):**

| Scenario | Risk Shift |
|----------|-----------|
| Drought Shock | +194 high-risk (+23.5%) |
| Combined Crisis | +117 high-risk (+16.3%) |
| Recovery Boom | -85 high-risk (-7.1%) |

Drought Index is the #1 feature at 28.6% importance — weather dominates financial ratios.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Streamlit |
| Backend | FastAPI + SQLAlchemy + SQLite |
| ML | scikit-learn Random Forest × 3 |
| Explainability | SHAP + Gemini AI |
| Deployment | Docker · HuggingFace Spaces · GitHub |

---

## Quick Start

```bash
git clone https://github.com/Uday-Kiran-01/AgriSense.git
cd Agri-Sense
pip install -r requirements.txt
cd backend && uvicorn app.main:app --reload
```

---

## Docs

- [Technical Write-up](docs/technical-writeup.md) — 12-page engineering document
- [Architecture Overview](docs/architecture.md) — Mermaid diagrams

---

## License

MIT · Advisory only — final lending decisions made by qualified humans.
