# 🌱 AgriSense AI

> **AI-Assisted Agricultural Lending Platform**

AgriSense AI doesn't try to automate lending decisions. It structures fragmented agricultural, financial, and environmental information into an explainable decision-support workflow. The platform combines deterministic financial analysis, machine learning predictions, seasonal liquidity modelling, scenario simulation, and peer benchmarking to help both farmers and lenders understand not only the predicted risk, but also why that risk exists and how it changes under different decisions.

> 🇸🇪 **Swedish Demo** — Synthetic data, SEK currency, GDPR compliant. 2,500 farm portfolio across 11 regions.

🔗 **Live:** [github.com/Uday-Kiran-01/AgriSense](https://github.com/Uday-Kiran-01/AgriSense)

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

### Offline Pipeline (Training)

```
Synthetic Data (2,500 farmers)
        │
        ▼
  Data Validation ─── rejects impossible values
        │
        ▼
  Data Cleaning ─── missing, duplicates, outliers (flag)
        │
        ▼
  Feature Engineering ─── 15 derived features
        │
        ▼
  Train/Test Split ─── 80/20 stratified
        │
        ▼
  Cross-Validation ─── 5-fold StratifiedKFold
        │
        ▼
  Grid Search ─── n_estimators, max_depth, min_samples_split
        │
        ▼
  Model Training ─── Random Forest × 3
        │
        ▼
  Evaluation ─── Precision, Recall, F1, ROC-AUC, Confusion Matrix
        │
        ▼
  Save Pipeline ─── model.pkl + metadata.json + feature_columns.json
```

### Online Pipeline (Inference)

```
New Farmer Application
        │
        ▼
  Load Saved Pipeline ─── same cleaning, same features, same model
        │
        ▼
  Document Upload ─── financial statements, loan docs, land records
        │
        ▼
  Data Extraction ─── structured values + provenance tracking
        │
        ▼
  Unified Farmer Profile ─── financial + operational + external
        │
  ┌─────┴─────┐
  ▼           ▼
Financial    External Data
Analysis     (Weather, Commodity, EU CAP)
  │           │
  └─────┬─────┘
        ▼
  Feature Engineering ─── SAME 15 features as training
        │
        ▼
  Load Model ─── Random Forest (scale-invariant, no transform needed)
        │
        ▼
  Prediction ─── risk score, repayment prob, debt capacity
        │
        ▼
  Explainability ─── feature importance rankings
        │
        ▼
  Scenario Analysis ─── what-if simulations
        │
        ▼
  Gemini AI ─── generates decision memo (never decides)
        │
        ▼
  Bank Loan Officer Dashboard ─── HUMAN MAKES FINAL DECISION
```

> ⚡ **Key design choice**: Training and inference use the **same preprocessing pipeline**. Median values, feature order, and encoding maps are saved during training and reloaded at inference — no train/serve skew.

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

## 🧱 Architecture Principles

### Separation of Concerns

| Layer | Responsibility | Example |
|---|---|---|
| **Validation** | Is the input usable? | Revenue >= 0. Interest rate 0-25%. |
| **Financial Analysis** | Compute objective metrics | DSCR = EBITDA / Debt Service. |
| **Machine Learning** | Learn patterns from data | Random Forest on 2,500 farmers. |
| **Gemini AI** | Explain in human language | "DSCR of 1.32x means..." |

> Business rules validate. Financial formulas calculate. ML predicts. Gemini explains.

### The Model Learns — We Don't Hardcode

8 farmer profiles with probabilistic outcomes. The model sees features, not profiles.

| Profile | % | Default Rate | What ML Learns |
|---|---|---|---|
| Established | 30% | ~5% | Strong repayment history + large farm + owned land → repayment likely |
| Conservative | 18% | ~4% | Low debt + stable income + insurance → low default risk |
| Expansion | 15% | ~18% | High leverage interacts with weather and commodity prices → mixed outcomes |
| Young Farmer | 12% | ~12% | Limited history interacts with farm size, cash flow, and UC score → variable risk |
| Diversified | 10% | ~7% | Multiple crops + premium prices → revenue stability → lower risk |
| Struggling | 8% | ~45% | Declining revenue + missed payments + low UC → elevated risk |
| Organic Premium | 5% | ~6% | Higher revenue/ha offsets higher costs → moderate risk |
| Tenant | 2% | ~15% | No land collateral + leased + variable costs → distinct risk pattern |

> The model never receives the profile label or the default probability. It only sees financial, operational, and environmental features. It discovers risk patterns from the data — including how "no credit history" interacts differently with strong vs. weak financials.

### Target Variable

The Random Forest predicts:
- **Credit Risk** (binary classifier): Will this farmer default? (0 = repays, 1 = defaults/high risk)
- **Repayment Probability** (regressor): Continuous 0–1 estimate
- **Debt Capacity** (regressor): Maximum additional loan amount (SEK)

Labels are generated probabilistically: a farmer from the "Struggling" profile has a ~45% chance of being labeled as default, not 100%. This creates realistic class overlap — some struggling farmers do repay, and some established farmers don't. The model must learn from patterns, not memorize profiles.

---

## 📋 Model Card

### Purpose
Predict repayment risk and debt capacity for Swedish agricultural businesses to **support — not replace — human lending decisions.**

### Training Data
2,500 synthetic Swedish agricultural businesses representing 8 portfolio profiles. All data is synthetic (no real PII). Dataset v1.0.

### Features (15)
| Category | Features |
|---|---|
| Financial | debt_to_income, dscr, operating_margin, cash_flow_margin, working_capital, interest_coverage |
| Leverage | loan_to_value, asset_coverage, debt_to_equity, current_ratio |
| Credit | repayment_ratio |
| Environmental | drought_index, price_change_abs |
| Operational | farm_size_ha, has_insurance |

### Target
- **Credit Risk**: Binary (0 = repays, 1 = defaults). Labels generated probabilistically per profile.
- **Repayment Probability**: Continuous 0–1.
- **Debt Capacity**: SEK, maximum additional loan amount.

### Model
Random Forest (scikit-learn). 3 separate models (classifier + 2 regressors). Hyperparameters tuned via GridSearchCV (n_estimators, max_depth, min_samples_split).

### Validation
5-fold StratifiedKFold cross-validation. Metrics: Precision, Recall, F1, ROC-AUC, Confusion Matrix. Optimized for recall (False Negatives = missed defaults = expensive).

### Limitations
- **Synthetic data** — patterns may differ from real-world agricultural lending
- **Simplified assumptions** — no macroeconomic shocks, no policy changes
- **Swedish context only** — not validated for other regions or regulatory regimes
- **Not suitable for production** lending decisions without real-data validation
- **CAP dependency**: Treats subsidies as farmer-level features. Does not model systemic policy changes (e.g., EU CAP reform) that would affect the entire portfolio simultaneously.
- **Portfolio correlation**: Evaluates farmers individually. Does not model correlated defaults across a lender's portfolio (e.g., all wheat farmers in Skåne affected by a single price collapse).
- **Land valuation**: Uses synthetic comparable-sales estimates (simplified ortsprismetoden). Real lending requires certified valuation.
- **FX exposure**: Not modeled. Grain exporters selling in EUR would be affected by SEK/EUR fluctuations.
- **Succession risk**: Not modeled. Average Swedish farmer age 55+. Farm transfer could affect debt servicing.
- **Model governance**: Version, training date, and validation metrics are tracked. Automated retraining and formal validation processes are documented as future work.

### Ethical Considerations
- All recommendations are **advisory** — final decisions remain with human loan officers
- No demographic features (age, gender, ethnicity) used as model inputs
- Synthetic dataset designed for representative coverage across farm sizes, regions, and credit profiles
- Model confidence is reported alongside predictions — low-confidence predictions are flagged for manual review
- Decision Readiness layer identifies insufficient evidence and recommends human intervention

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

Current demo uses synthetic data (dataset v1.0: 2,500 Swedish farmers). For production:

- **Missing financials**: Median imputation by farm size bracket — preserves distribution per cohort. Same medians saved at training time and reused at inference.
- **Missing weather**: API backfill from SMHI/OpenWeatherMap with fallback to 5-year regional average.
- **Conflicting documents**: Revenue mismatch >10% across documents = automatic flag for manual review. System presents both values with sources — never auto-resolves.
- **Invalid values**: Rejected at validation boundary — never silently corrected. Loan officer is notified of the specific field and violation.
- **Pipeline consistency**: Same preprocessing used during training is reused during inference. No train/serve skew.
- **Feature store**: All 15 features computed deterministically from raw inputs — reproducible predictions, auditable at any point.

### ⚖️ Data Leakage Prevention

Only information available **before** a loan decision is used as input features. Future repayment outcomes serve exclusively as training labels — never as input features. The train/test split respects temporal ordering: no future data appears in training. This is critical for lending models where look-ahead bias would produce unrealistically optimistic evaluations.

### 🎯 Configurable Risk Threshold

The default classification threshold is 0.50, but this is **configurable** per bank policy:

| Threshold | Behavior | Use Case |
|---|---|---|
| 0.35 | More approvals, higher recall | Growth-focused lending |
| **0.50** | **Balanced (default)** | **Standard portfolio** |
| 0.65 | Conservative, more manual reviews | Risk-averse lending |

Risk scores >0.65 trigger an automatic **Manual Review Required** flag regardless of threshold.

### 🌍 Bias Awareness

The synthetic dataset was generated with representative distributions across Swedish regions (Skåne, Västra Götaland, Östergötland, etc.), farm sizes (10–500 ha), crop types, and credit profiles (UC scores 350–890). No demographic features (age, gender, ethnicity) are used as model inputs — only financial, operational, and environmental indicators.

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
