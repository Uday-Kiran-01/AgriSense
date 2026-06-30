"""
ML Service — Random Forest model for credit risk, repayment, and debt capacity.
Trains on database farmers if available, falls back to numpy synthetic data.
"""
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(settings.MODEL_PATH)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RISK_MODEL_PATH = MODEL_DIR / "credit_risk_model.pkl"
REPAY_MODEL_PATH = MODEL_DIR / "repayment_model.pkl"
CAPACITY_MODEL_PATH = MODEL_DIR / "debt_capacity_model.pkl"

FEATURE_NAMES = [
    "debt_to_income", "dscr", "working_capital_100k", "operating_margin",
    "loan_to_value", "asset_coverage", "current_ratio", "debt_to_equity",
    "cash_flow_margin", "interest_coverage", "repayment_ratio",
    "drought_index", "price_change_abs", "farm_size_ha", "has_insurance",
]


def engineer_features(financial_ratios: dict, external_data: dict,
                      operational_data: dict | None = None,
                      existing_loans: list | None = None) -> np.ndarray:
    """
    Engineer ML features from financial ratios, external data, and operational data.

    Returns a 2D numpy array ready for model prediction.
    """
    loans = existing_loans or []

    # Repayment history
    total_on_time = sum(l.get("on_time_payments", 0) for l in loans)
    total_due = sum(l.get("total_payments_due", 1) for l in loans)
    repayment_ratio = total_on_time / max(total_due, 1)

    # Extract features in consistent order
    features = [
        financial_ratios.get("debt_to_income", 0),
        financial_ratios.get("dscr", 1),
        financial_ratios.get("working_capital", 0) / 100000,  # scale to lakhs
        financial_ratios.get("operating_margin", 0),
        financial_ratios.get("loan_to_value", 0),
        financial_ratios.get("asset_coverage", 1),
        financial_ratios.get("current_ratio", 1),
        financial_ratios.get("debt_to_equity", 0),
        financial_ratios.get("cash_flow_margin", 0),
        financial_ratios.get("interest_coverage", 1),
        repayment_ratio,
        external_data.get("weather", {}).get("drought_index", 0),
        abs(external_data.get("commodity", {}).get("price_change_pct", 0)) / 100,
        operational_data.get("farm_size_acres", 0) if operational_data else 0,
        1 if operational_data and operational_data.get("has_insurance") else 0,
    ]

    logger.debug(f"Engineered {len(features)} features")
    return np.array(features).reshape(1, -1)


def load_or_train_models(force_retrain: bool = False) -> tuple:
    """
    Load trained models from disk, or train new ones.
    Uses database farmers for training if available (>100 farmers),
    otherwise falls back to synthetic numpy data.

    Set force_retrain=True to retrain even if models exist on disk.
    """
    if os.path.exists(RISK_MODEL_PATH) and not force_retrain:
        logger.info("Loading existing ML models from disk...")
        risk_model = joblib.load(RISK_MODEL_PATH)
        repay_model = joblib.load(REPAY_MODEL_PATH)
        capacity_model = joblib.load(CAPACITY_MODEL_PATH)
        return risk_model, repay_model, capacity_model

    # Try training from database first
    try:
        from ..database import SessionLocal
        from ..models import Farmer, FinancialRecord, ExistingLoan, OperationalData
        from .financial_analysis import calculate_financial_ratios

        db = SessionLocal()
        farmer_count = db.query(Farmer).count()

        if farmer_count >= 100:
            logger.info(f"Training ML models from {farmer_count} database farmers...")
            return _train_from_database(db, farmer_count)
        else:
            logger.info(f"Only {farmer_count} farmers in DB — using synthetic training data...")
            db.close()
            return _train_from_synthetic()
    except Exception as e:
        logger.warning(f"Database training failed: {e}. Using synthetic data.")
        return _train_from_synthetic()


def _to_int(val) -> int:
    """Safely convert SQLite values (may be bytes) to int."""
    if val is None:
        return 0
    if isinstance(val, bytes):
        return int.from_bytes(val, 'little')
    return int(val)


def _to_float(val) -> float:
    """Safely convert SQLite values to float."""
    if val is None:
        return 0.0
    if isinstance(val, bytes):
        import struct
        return struct.unpack('d', val)[0]
    return float(val)


def _train_from_database(db, farmer_count: int) -> tuple:
    """Train models using data from all farmers in the database."""
    from ..models import Farmer, FinancialRecord, ExistingLoan, OperationalData
    from .financial_analysis import calculate_financial_ratios

    farmers = db.query(Farmer).all()
    X_rows = []
    y_risk = []
    y_repay = []
    y_capacity = []

    for farmer in farmers:
        financials = (
            db.query(FinancialRecord)
            .filter(FinancialRecord.farmer_id == farmer.id)
            .order_by(FinancialRecord.year.desc())
            .all()
        )
        loans = (
            db.query(ExistingLoan)
            .filter(ExistingLoan.farmer_id == farmer.id)
            .all()
        )
        ops = (
            db.query(OperationalData)
            .filter(OperationalData.farmer_id == farmer.id)
            .first()
        )

        if not financials:
            continue

        ratios = calculate_financial_ratios(
            [r.__dict__ for r in financials],
            [l.__dict__ for l in loans],
            ops.__dict__ if ops else None,
        )

        # Repayment history — defensive type conversion for SQLite
        total_on_time = sum(_to_int(l.on_time_payments) for l in loans)
        total_due = sum(_to_int(l.total_payments_due) for l in loans)
        repayment_ratio = total_on_time / max(total_due, 1)

        # Feature vector (same order as FEATURE_NAMES)
        features = [
            _to_float(ratios.get("debt_to_income", 0)),
            _to_float(ratios.get("dscr", 1)),
            _to_float(ratios.get("working_capital", 0)) / 100000,
            _to_float(ratios.get("operating_margin", 0)),
            _to_float(ratios.get("loan_to_value", 0)),
            _to_float(ratios.get("asset_coverage", 1)),
            _to_float(ratios.get("current_ratio", 1)),
            _to_float(ratios.get("debt_to_equity", 0)),
            _to_float(ratios.get("cash_flow_margin", 0)),
            _to_float(ratios.get("interest_coverage", 1)),
            float(repayment_ratio),
            0.25,
            0.03,
            _to_float(ops.farm_size_acres if ops else 20),
            float(1 if ops and ops.has_insurance else 0),
        ]

        # Target: risk
        dti = _to_float(ratios.get("debt_to_income", 0))
        dscr = _to_float(ratios.get("dscr", 1))
        uc = _to_int(farmer.cibil_score) if farmer.cibil_score else 600
        is_risky = 1 if (dti > 0.50 or dscr < 1.25 or uc < 550) else 0

        # Target: repayment probability (sigmoid of financial health)
        repay_prob = 1 / (1 + np.exp(-(dscr - 1.0) * 2 - (1 - dti) * 3 + (uc / 600 - 1)))

        # Target: debt capacity
        ebitda = _to_float(ratios.get("ebitda", 200000))
        total_debt = sum(_to_float(l.outstanding_balance) for l in loans)
        capacity = max(0, (ebitda * 2.5 - total_debt) * 0.6)
        capacity += np.random.normal(0, capacity * 0.1)

        X_rows.append(features)
        y_risk.append(is_risky)
        y_repay.append(_clamp(repay_prob, 0.01, 0.99))
        y_capacity.append(max(0, capacity))

    db.close()

    X = np.array(X_rows)
    y_risk = np.array(y_risk)
    y_repay = np.array(y_repay)
    y_capacity = np.array(y_capacity)

    logger.info(f"Training on {len(X)} samples from database")

    return _fit_and_save_models(X, y_risk, y_repay, y_capacity)


def _train_from_synthetic() -> tuple:
    """Fallback: train on numpy synthetic data (200 samples)."""
    np.random.seed(42)
    n = 200

    X = np.column_stack([
        np.random.uniform(0.1, 0.7, n),
        np.random.uniform(0.5, 3.0, n),
        np.random.uniform(-5, 20, n),
        np.random.uniform(0.05, 0.55, n),
        np.random.uniform(0.05, 0.8, n),
        np.random.uniform(0.5, 5.0, n),
        np.random.uniform(0.5, 4.0, n),
        np.random.uniform(0.1, 2.5, n),
        np.random.uniform(0.05, 0.5, n),
        np.random.uniform(0.5, 10.0, n),
        np.random.uniform(0.3, 1.0, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 0.15, n),
        np.random.uniform(2, 30, n),
        np.random.choice([0, 1], n),
    ])

    y_risk = (
        (X[:, 0] * 2.0 + (1 / np.maximum(X[:, 1], 0.1)) * 0.5 +
         X[:, 11] * 1.5 + (1 - X[:, 14]) * 0.3 +
         np.random.normal(0, 0.1, n))
    )
    y_risk = (y_risk > np.median(y_risk)).astype(int)

    y_repay = (
        0.9 - X[:, 0] * 0.3 + X[:, 1] * 0.05 + X[:, 10] * 0.2 -
        X[:, 11] * 0.1 + (1 - X[:, 14]) * 0.05 +
        np.random.normal(0, 0.05, n)
    )
    y_repay = np.clip(y_repay, 0.01, 0.99)

    y_capacity = (
        800000 - X[:, 0] * 600000 + X[:, 1] * 150000 +
        X[:, 3] * 400000 - X[:, 4] * 500000 -
        X[:, 11] * 200000 + np.random.normal(0, 50000, n)
    )
    y_capacity = np.clip(y_capacity, 0, 2000000)

    logger.info(f"Training on {n} synthetic samples (fallback)")

    return _fit_and_save_models(X, y_risk, y_repay, y_capacity)


def _fit_and_save_models(X, y_risk, y_repay, y_capacity) -> tuple:
    """Train and save all three models."""
    risk_model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    risk_model.fit(X, y_risk)

    repay_model = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    repay_model.fit(X, y_repay)

    capacity_model = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    capacity_model.fit(X, y_capacity)

    # Save
    joblib.dump(risk_model, RISK_MODEL_PATH)
    joblib.dump(repay_model, REPAY_MODEL_PATH)
    joblib.dump(capacity_model, CAPACITY_MODEL_PATH)

    logger.info(f"Models trained on {len(X)} samples, saved to {MODEL_DIR}")
    logger.info(f"  Risk model classes: {risk_model.classes_.tolist()}")
    logger.info(f"  Feature count: {X.shape[1]}")

    return risk_model, repay_model, capacity_model


def _clamp(value, low, high):
    return max(low, min(high, value))


def predict(features: np.ndarray) -> dict:
    """
    Run all three models and return predictions with feature importance.
    """
    risk_model, repay_model, capacity_model = load_or_train_models()

    # Predict
    risk_prob = float(risk_model.predict_proba(features)[0][1])
    repay_prob = float(repay_model.predict(features)[0])
    debt_capacity = max(0, float(capacity_model.predict(features)[0]))

    # Feature importance
    risk_importance = risk_model.feature_importances_
    repay_importance = repay_model.feature_importances_
    capacity_importance = capacity_model.feature_importances_
    avg_importance = (risk_importance + repay_importance + capacity_importance) / 3

    importance_dict = dict(
        sorted(zip(FEATURE_NAMES, avg_importance), key=lambda x: x[1], reverse=True)
    )

    # Risk breakdown
    def classify_risk(prob: float) -> str:
        if prob < 0.3:
            return "low"
        elif prob < 0.55:
            return "medium"
        else:
            return "high"

    # Use actual feature values for risk classification
    dti = features[0][0]
    dscr = features[0][1]
    drought = features[0][11]
    price_change = features[0][12]

    financial_health_risk = classify_risk(dti * 1.5 + max(0, (1.25 - dscr)) * 0.5)
    environmental_risk = classify_risk(drought)
    market_risk = classify_risk(price_change * 5)

    overall = "low"
    if "high" in [financial_health_risk, environmental_risk, market_risk]:
        overall = "high"
    elif "medium" in [financial_health_risk, environmental_risk, market_risk]:
        overall = "medium"

    logger.info(f"Prediction: risk={risk_prob:.2f}, repay={repay_prob:.2f}, "
                f"capacity={debt_capacity:,.0f} kr, overall={overall}")

    return {
        "credit_risk_score": round(risk_prob, 4),
        "repayment_probability": round(repay_prob, 4),
        "debt_capacity": round(debt_capacity, 2),
        "model_confidence": 0.85,
        "model_version": "v1.1.0",
        "feature_importance": importance_dict,
        "financial_health_risk": financial_health_risk,
        "environmental_risk": environmental_risk,
        "market_risk": market_risk,
        "overall_financing_risk": overall,
    }
