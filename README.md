# 🌱 AgriSense AI

**Explainable Decision Support for Agricultural Lending**

[![Live Demo](https://img.shields.io/badge/demo-HF%20Spaces-blue)](https://huggingface.co/spaces/SuperNitro/Agri-Sense)
[![CI/CD](https://img.shields.io/badge/deploy-GitHub%20Actions-green)](https://github.com/Uday-Kiran-01/AgriSense/actions)

---

AgriSense AI combines financial data, operational records, and environmental signals into a transparent agricultural lending workflow. It never approves loans - it prepares evidence for humans who do.

> 🇸🇪 Swedish demo · Synthetic data · SEK · GDPR compliant · 8 demo farmers

---

## The Workflow

Three roles. One application. The full lending lifecycle.

| Role | What they see | What they do |
|------|-------------|-------------|
| 👨‍🌾 **Farmer** | Their application only | 5-step wizard → Submit → Track status → See decision |
| 🏢 **Credit Analyst** | All submitted applications | Filter pipeline → Review ratios → Run scenarios → Generate memo → Send to bank |
| 🏦 **Bank Officer** | Applications escalated to them | Review full package → Approve / Conditions / Reject |

**Pipeline:** Draft → Submitted → In Review → Sent to Bank → Approved/Rejected

---

## How It Works

A standalone Streamlit app with the ML model embedded directly.

```
Farmer enters crop, hectares, insurance
        ↓
current_financials() - scales baseline by farmer inputs
        ↓
ratios() - 10 standard financial formulas (DSCR, DTI, OM, LTV, etc.)
        ↓
predict() - 15 features → Random Forest × 3 → risk%, repay%, capacity
        ↓
Memo - computed from actual ratios and predictions
        ↓
Bank officer makes the final call
```

The analyst workspace has a 7-tab view (8 for bank with the Decision tab). Everything fits on one page - no scrolling between sections.

---

## ML Performance

Random Forest × 3 on 15 engineered features. Evaluated on 1,000 unseen farmers with shifted distributions.

| Metric | Value |
|--------|-------|
| Accuracy | 80.1% |
| Precision | 99.4% |
| ROC-AUC | 90.0% |

Drought Index is the top feature at 28.6% importance - weather dominates financial ratios. This means drought insurance and irrigation investment become quantitative lending factors, not just qualitative ones.

---

## Running It

```bash
# Option 1: Local
git clone https://github.com/Uday-Kiran-01/AgriSense.git
cd Agri-Sense && pip install -r requirements.txt && streamlit run app.py

# Option 2: Docker
docker compose up
```

---

## Deploying

Every `git push` to `main` triggers a GitHub Actions workflow that auto-deploys to HF Spaces. The pipeline uploads `app.py`, `requirements.txt`, `.streamlit/config.toml`, and `agrisense_model_bundle.pkl`. Deploy time: ~30 seconds.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.36 |
| ML | scikit-learn Random Forest × 3 (joblib) |
| Storage | SQLite for custom farmer persistence |
| State | st.session_state overrides (survive Streamlit reruns) |
| CI/CD | GitHub Actions → HF Spaces |
| Container | Docker + Docker Compose |
| Backend (prod) | FastAPI + SHAP + Gemini (available in repo) |

---

## Docs

- [Technical Write-up](docs/technical-writeup.md) - 12-section engineering document covering design, ML, evaluation, and implementation
- [Architecture Overview](docs/architecture.md) - System architecture with Mermaid diagrams

---

## License

MIT · Advisory only - final lending decisions made by qualified humans.
