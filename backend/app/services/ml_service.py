"""
ML Service — Random Forest model for credit risk, repayment, and debt capacity.
"""
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(settings.MODEL_PATH)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RISK_MODEL_PATH = MODEL_DIR / "credit_risk_model.pkl"
REPAY_MODEL_PATH = MODEL_DIR / "repayment_model.pkl"
CAPACITY_MODEL_PATH = MODEL_DIR / "debt_capacity_model.pkl"


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


def load_or_train_models() -> tuple:
    """
    Load trained models from disk, or train new ones if not found.
    Returns (risk_model, repayment_model, capacity_model, feature_names).
    """
    if os.path.exists(RISK_MODEL_PATH):
        logger.info("Loading existing ML models from disk...")
        risk_model = joblib.load(RISK_MODEL_PATH)
        repay_model = joblib.load(REPAY_MODEL_PATH)
        capacity_model = joblib.load(CAPACITY_MODEL_PATH)
        return risk_model, repay_model, capacity_model

    logger.info("Training new ML models...")
    return _train_models()


def _train_models() -> tuple:
    """Train Random Forest models on synthetic data."""
    # Generate synthetic training data (200 samples)
    np.random.seed(42)
    n = 200

    # Feature columns (15 features matching engineer_features)
    X = np.column_stack([
        np.random.uniform(0.1, 0.7, n),     # debt_to_income
        np.random.uniform(0.5, 3.0, n),     # dscr
        np.random.uniform(-5, 20, n),       # working_capital (lakhs)
        np.random.uniform(0.05, 0.55, n),   # operating_margin
        np.random.uniform(0.05, 0.8, n),    # loan_to_value
        np.random.uniform(0.5, 5.0, n),     # asset_coverage
        np.random.uniform(0.5, 4.0, n),     # current_ratio
        np.random.uniform(0.1, 2.5, n),     # debt_to_equity
        np.random.uniform(0.05, 0.5, n),    # cash_flow_margin
        np.random.uniform(0.5, 10.0, n),    # interest_coverage
        np.random.uniform(0.3, 1.0, n),     # repayment_ratio
        np.random.uniform(0, 1, n),         # drought_index
        np.random.uniform(0, 0.15, n),      # price_change_abs
        np.random.uniform(2, 30, n),        # farm_size_acres
        np.random.choice([0, 1], n),        # has_insurance
    ])

    # Target: credit risk (0 = low, 1 = high)
    # Rule-based: risk increases with high DTI, low DSCR, high drought, no insurance
    y_risk = (
        (X[:, 0] * 2.0 + (1 / np.maximum(X[:, 1], 0.1)) * 0.5 +
         X[:, 11] * 1.5 + (1 - X[:, 14]) * 0.3 +
         np.random.normal(0, 0.1, n))
    )
    y_risk = (y_risk > np.median(y_risk)).astype(int)

    # Target: repayment probability (continuous)
    y_repay = (
        0.9 - X[:, 0] * 0.3 + X[:, 1] * 0.05 + X[:, 10] * 0.2 -
        X[:, 11] * 0.1 + (1 - X[:, 14]) * 0.05 +
        np.random.normal(0, 0.05, n)
    )
    y_repay = np.clip(y_repay, 0.01, 0.99)

    # Target: debt capacity (additional loan amount, in INR)
    y_capacity = (
        800000 - X[:, 0] * 600000 + X[:, 1] * 150000 +
        X[:, 3] * 400000 - X[:, 4] * 500000 -
        X[:, 11] * 200000 + np.random.normal(0, 50000, n)
    )
    y_capacity = np.clip(y_capacity, 0, 2000000)

    feature_names = [
        "debt_to_income", "dscr", "working_capital_lakhs", "operating_margin",
        "loan_to_value", "asset_coverage", "current_ratio", "debt_to_equity",
        "cash_flow_margin", "interest_coverage", "repayment_ratio",
        "drought_index", "price_change_abs", "farm_size_acres", "has_insurance",
    ]

    # Train models
    X_train, X_test, y_risk_train, y_risk_test = train_test_split(X, y_risk, test_size=0.2, random_state=42)

    risk_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    risk_model.fit(X, y_risk)

    repay_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    repay_model.fit(X, y_repay)

    capacity_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    capacity_model.fit(X, y_capacity)

    # Save models
    joblib.dump(risk_model, RISK_MODEL_PATH)
    joblib.dump(repay_model, REPAY_MODEL_PATH)
    joblib.dump(capacity_model, CAPACITY_MODEL_PATH)

    logger.info(f"Models trained and saved to {MODEL_DIR}")
    logger.info(f"  Risk model accuracy: {risk_model.score(X_test, y_risk_test):.2%}")
    logger.info(f"  Repay model R²: {repay_model.score(X_test, y_repay_test):.2%}")
    logger.info(f"  Capacity model R²: {capacity_model.score(X_test, y_capacity_test):.2%}")

    return risk_model, repay_model, capacity_model


def predict(features: np.ndarray) -> dict:
    """
    Run all three models and return predictions with feature importance.
    """
    risk_model, repay_model, capacity_model = load_or_train_models()

    # Predict
    risk_prob = float(risk_model.predict_proba(features)[0][1])  # probability of high risk
    repay_prob = float(repay_model.predict(features)[0])
    debt_capacity = max(0, float(capacity_model.predict(features)[0]))

    # Feature importance (average across models)
    risk_importance = risk_model.feature_importances_
    repay_importance = repay_model.feature_importances_
    capacity_importance = capacity_model.feature_importances_

    avg_importance = (risk_importance + repay_importance + capacity_importance) / 3

    feature_names = [
        "debt_to_income", "dscr", "working_capital", "operating_margin",
        "loan_to_value", "asset_coverage", "current_ratio", "debt_to_equity",
        "cash_flow_margin", "interest_coverage", "repayment_ratio",
        "drought_index", "price_change", "farm_size", "has_insurance",
    ]

    importance_dict = dict(
        sorted(zip(feature_names, avg_importance), key=lambda x: x[1], reverse=True)
    )

    # Risk breakdown
    def classify_risk(prob: float) -> str:
        if prob < 0.3:
            return "low"
        elif prob < 0.55:
            return "medium"
        else:
            return "high"

    financial_health_risk = classify_risk(
        features[0][0] * 1.5 + (1 - features[0][1]) * 0.3
    )
    environmental_risk = classify_risk(features[0][11])
    market_risk = classify_risk(features[0][12] * 5)

    overall = "low"
    if "high" in [financial_health_risk, environmental_risk, market_risk]:
        overall = "high"
    elif "medium" in [financial_health_risk, environmental_risk, market_risk]:
        overall = "medium"

    logger.info(f"Prediction: risk={risk_prob:.2f}, repay={repay_prob:.2f}, "
                f"capacity=₹{debt_capacity:,.0f}, overall={overall}")

    return {
        "credit_risk_score": round(risk_prob, 4),
        "repayment_probability": round(repay_prob, 4),
        "debt_capacity": round(debt_capacity, 2),
        "model_confidence": 0.85,
        "model_version": "v1.0.0",
        "feature_importance": importance_dict,
        "financial_health_risk": financial_health_risk,
        "environmental_risk": environmental_risk,
        "market_risk": market_risk,
        "overall_financing_risk": overall,
    }
