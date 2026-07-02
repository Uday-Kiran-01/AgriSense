# 🌱 AgriSense AI

**Explainable Decision Support for Agricultural Lending**

Live demo: [huggingface.co/spaces/SuperNitro/Agri-Sense](https://huggingface.co/spaces/SuperNitro/Agri-Sense)

---

AgriSense AI combines financial, operational, and environmental data into a transparent lending workflow. It never approves loans — it prepares evidence for humans who do.

> 🇸🇪 Swedish demo · Synthetic data · SEK currency · GDPR compliant · 8 demo farmers · 11 regions

---

## What It Does

| Role | Workflow |
|------|----------|
| 👨‍🌾 **Farmer** | 5-step wizard → Submit to Credit Analyst → Track status → See bank decision |
| 🏢 **Credit Analyst** | Pipeline with filters → 7-tab review workspace → Financial ratios → Scenario sim → Memo → Send to Bank |
| 🏦 **Bank Officer** | Pipeline → 8-tab workspace with Decision tab → Approve / Conditions / Reject |

**Pipeline:** Draft → Submitted → In Review → Sent to Bank → Approved/Rejected

---

## Architecture

Standalone Streamlit app (`app.py`, ~1,400 lines) — no backend required for the demo.

```
Farmer/Analyst/Bank → Streamlit UI → Embedded ML (RF×3 via joblib) → SQLite farmers
                                      ↓
                              session_state (pipeline overrides, farmer profiles)
```

- **8-tab timeline** (7 for analyst, 8 for bank) — single-page layout
- **SQLite persistence** — custom farmers survive restarts
- **session_state** — status overrides + farmer profiles survive Streamlit reruns

---

## ML Approach

**Random Forest × 3** — embedded via `agrisense_model_bundle.pkl` (9.7 MB joblib).

| Principle | Implementation |
|-----------|---------------|
| Deterministic + ML | 10 financial ratios computed from formulas, ML for risk estimation |
| Honest evaluation | 1,000 unseen farmers, 5 stress scenarios |
| Human-in-the-loop | AI prepares evidence — humans decide |

**Evaluation (1,000 unseen farmers, shifted distributions):**

| Metric | Value |
|--------|-------|
| Accuracy | 80.1% |
| Precision | 99.4% |
| Recall | 70.9% |
| F1 | 82.8% |
| ROC-AUC | 90.0% |

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Streamlit 1.36 |
| ML | scikit-learn Random Forest × 3 |
| Storage | SQLite (built-in) |
| State | st.session_state overrides |
| Deployment | HuggingFace Spaces · GitHub |
| Backend (future) | FastAPI + SHAP + Gemini |

---

## Quick Start

```bash
git clone https://github.com/Uday-Kiran-01/AgriSense.git
cd Agri-Sense
pip install -r requirements.txt
streamlit run app.py
```

---

## Docs

- [Technical Write-up](docs/technical-writeup.md) — 12-section engineering document
- [Architecture Overview](docs/architecture.md) — Mermaid diagrams

| Scenario | Risk Shift |
| Deployment | HuggingFace Spaces · GitHub |
| Backend (future) | FastAPI + SHAP + Gemini |

---

## Quick Start

```bash
git clone https://github.com/Uday-Kiran-01/AgriSense.git
cd Agri-Sense
pip install -r requirements.txt
streamlit run app.py
```

---

## Docs

- [Technical Write-up](docs/technical-writeup.md) — 12-page engineering document
- [Architecture Overview](docs/architecture.md) — Mermaid diagrams

---

## License

MIT · Advisory only — final lending decisions made by qualified humans.
