# 🌱 AgriSense AI

> **Explainable AI Decision Support Platform for Agricultural Finance**

AgriSense AI helps farmers and financial institutions make transparent financing decisions by transforming fragmented financial, operational, and environmental data into explainable AI-powered decision support.

> 🇸🇪 **Swedish Demo** — This demo uses synthetic Swedish agricultural data with SEK (kr) currency. All personal data is fictional. GDPR compliant by design.

---
## 🔒 GDPR & Data Privacy

- **All data is synthetic** — No real personal data, names, addresses, or financial figures
- **Fictional farmer identity** — "Erik Johansson" is a constructed persona
- **No persistent PII** — The SQLite database contains only demo data, wiped on restart
- **No tracking or cookies** — The Streamlit dashboard has no analytics
- **Document references are placeholders** — No real PDFs or uploaded files
- **Swedish context** — UC credit scores, Landshypotek/Swedbank lenders, EU CAP subsidies

---

## 🏗️ Architecture

```
                 Farmer
                    │
                    ▼
           Farmer Digital Vault
                    │
                    ▼
           Data Extraction Layer
                    │
                    ▼
          Unified Farmer Profile
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
 Financial Analysis      External Data
   (Ratios & KPIs)       (Weather, Commodity)
        │                        │
        └───────────┬────────────┘
                    ▼
         Explainable ML Engine
          (Random Forest)
                    │
                    ▼
          Scenario Analysis
         ("What-if" Engine)
                    │
                    ▼
           Gemini AI Layer
        (Explanations & Memo)
                    │
                    ▼
           Bank Loan Officer
               Dashboard
                    │
                    ▼
         Human Makes Decision
```

---

## 🎯 Oscar's Questions — Answered

| Question | Module |
|---|---|
| Combine financial, operational & environmental data | Unified Farmer Profile + External Data |
| Estimate debt capacity & repayment ability transparently | Financial Analysis Engine + Explainable ML |
| Scenario analysis for investment decisions | Scenario Analysis Engine |
| Weather, commodity prices, production data in risk models | External Data APIs + Feature Engineering |
| ML/statistical methods to find patterns | Random Forest + Feature Importance |
| Transform heterogeneous data into decision-support tools | Decision Memo + Streamlit Dashboard |

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **Database** | SQLite + SQLAlchemy |
| **ML** | Random Forest (scikit-learn) |
| **Explainability** | Feature Importance (SHAP-ready) |
| **AI** | Gemini API (explanations only, never decisions) |
| **External APIs** | OpenWeatherMap, Alpha Vantage (mock fallback) |
| **Containerization** | Docker |
| **Deployment** | Hugging Face Spaces |
| **Config** | `.env` |
| **Logging** | Python logging |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/Uday-Kiran-01/AgriSense.git
cd AgriSense

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure (Optional)

```bash
cp .env.example .env
# Edit .env with your API keys (optional — works without them)
```

### 3. Run Backend

```bash
uvicorn backend.app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Run Frontend

```bash
streamlit run frontend/app.py
```

Dashboard available at: http://localhost:8501

### 5. Docker (Alternative)

```bash
docker-compose up --build
```

---

## 📁 Project Structure

```
AgriSense/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── config.py            # Settings (.env)
│       ├── database.py          # SQLAlchemy + SQLite
│       ├── logger.py            # Centralized logging
│       ├── models/              # SQLAlchemy models
│       │   ├── farmer.py
│       │   ├── document.py
│       │   ├── loan.py
│       │   ├── financial.py
│       │   ├── operational.py
│       │   ├── external.py
│       │   ├── prediction.py
│       │   ├── scenario.py
│       │   └── memo.py
│       ├── schemas/             # Pydantic schemas
│       ├── routers/
│       │   └── agrisense.py     # All API endpoints
│       └── services/
│           ├── seed.py          # Demo data seeder
│           ├── external_data.py # Weather/commodity APIs
│           ├── financial_analysis.py  # Ratio calculations
│           ├── ml_service.py    # Random Forest models
│           ├── scenario_analysis.py   # What-if engine
│           └── gemini_service.py      # AI explanations
├── frontend/
│   └── app.py                   # Streamlit dashboard
├── data/                        # SQLite DB, models, logs
├── notebooks/                   # Jupyter notebooks
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📊 Key Features

### 🔐 Digital Farmer Vault
Centralized document storage for all financing-related documents — balance sheets, bank statements, loan agreements, land records, crop reports, insurance.

### 💰 Financial Analysis Engine
Calculates 10+ financial ratios:
- Debt-to-Income Ratio
- Debt Service Coverage Ratio (DSCR)
- Working Capital
- Operating Margin
- Loan-to-Value
- Asset Coverage
- Current Ratio
- Debt-to-Equity
- Cash Flow Margin
- Interest Coverage

### 🤖 Explainable ML
Random Forest models predict:
- **Credit Risk Score** (0-1)
- **Repayment Probability** (0-1)
- **Additional Debt Capacity** (₹)

Every prediction includes feature importance rankings.

### 🔮 Scenario Analysis
Simulate "what-if" scenarios:
- Rainfall decrease
- Commodity price drops
- New loan obligations
- Interest rate hikes
- Fuel price increases
- Tractor purchase

### 📝 AI Decision Memo
Gemini AI generates structured memos summarizing financial position, risks, model predictions, and supporting evidence. **The final lending decision is always human.**

### 🔬 Data Quality & ML Engineering Pipeline

The full preprocessing and ML pipeline runs before any prediction:

| Step | Method | Design Rationale |
|---|---|---|
| **1. Validation** | Rule-based checks (min/max bounds) | Rejects impossible values (e.g., negative revenue, 80% interest rate) |
| **2. Missing Values** | Strategy varies by data type | Median imputation for financials, mode for operational, API backfill for weather |
| **3. Duplicates** | Hash-based key detection | Prevents double-counting financial records |
| **4. Outliers** | IQR method — **flag only** | Never auto-removes. Banks need manual review of anomalies |
| **5. Standardization** | Currency, unit, date conversion | SEK/EUR/USD → SEK, acres → hectares, ISO dates |
| **6. Ambiguity** | Cross-document field comparison | Conflicting revenue across documents → flagged for review |
| **7. Feature Engineering** | 15 derived features | Debt Ratio, Revenue/Ha, Rainfall Deviation, Repayment Ratio, etc. |
| **8. Scaling** | **Intentionally skipped** | Random Forest is scale-invariant (tree-based). Documented choice |
| **9. Encoding** | Label Encoding | Preferred for tree models. OneHot would increase dimensionality |
| **10. Train/Test** | 80/20 stratified split | Maintains class balance in both sets |
| **11. Cross-Validation** | 5-fold StratifiedKFold | More robust than single split. Reports mean ± std |
| **12. Hyperparameters** | GridSearchCV | Searches n_estimators, max_depth, min_samples_split |
| **13. Evaluation** | Precision, Recall, F1, ROC-AUC, Confusion Matrix | FP = lost business. FN = default risk. Optimized for recall |

> **Why Random Forest doesn't need scaling**: Tree-based models split on individual feature thresholds independent of scale. Unlike SVM, neural networks, or linear models, RF handles raw SEK values and ratios (0-1) simultaneously without normalization.

### 🛡️ Data Engineering for Real-World Deployment

Current demo uses synthetic data. For production:

- **Missing financials**: Median imputation by farm size bracket — preserves distribution per cohort
- **Missing weather**: API backfill from SMHI/OpenWeatherMap with fallback to 5-year regional average
- **Conflicting documents**: Revenue mismatch >10% across documents = automatic flag for manual review
- **Invalid values**: Rejected at validation boundary — never silently corrected
- **Pipeline consistency**: Same preprocessing used during training is reused during inference (no train/serve skew)
- **Feature store**: All 15 features computed deterministically from raw inputs — reproducible predictions

---

## 🔮 Future Work

- OCR document extraction (Pytesseract)
- Real-time weather API integration
- Commodity market feeds
- Credit bureau integration (CIBIL)
- Open Banking integration
- Government land registry integration
- Loan monitoring after approval
- Automated model retraining

---

## ⚠️ Disclaimer

AgriSense AI is a **decision-support tool**, not an autonomous decision-making system. All lending decisions must be made by qualified human loan officers following their institution's credit policies and regulatory requirements.

---

## 📄 License

MIT

---

<p align="center">
  <sub>Built with 🌱 for agricultural finance transparency</sub>
</p>
