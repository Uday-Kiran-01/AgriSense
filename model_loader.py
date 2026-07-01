"""
Standalone model loader for AgriSense AI.
Use this in any Streamlit app without needing the FastAPI backend.

Usage:
    from model_loader import load_model, predict

    bundle = load_model()
    result = predict(bundle, features_2d_array)
"""
import joblib
from pathlib import Path
import numpy as np

_MODEL_PATH = Path(__file__).resolve().parent / "agrisense_model_bundle.pkl"


def load_model():
    """Load the AgriSense model bundle."""
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model bundle not found at {_MODEL_PATH}. "
            f"Run bundle_models.py from the Agri-Sense project first."
        )
    return joblib.load(_MODEL_PATH)


def predict(bundle: dict, features: np.ndarray):
    """
    Run all 3 models on a feature array.

    Args:
        bundle: Loaded model bundle dict
        features: 2D numpy array (1, 15) with features in order:
            debt_to_income, dscr, working_capital_100k, operating_margin,
            loan_to_value, asset_coverage, current_ratio, debt_to_equity,
            cash_flow_margin, interest_coverage, repayment_ratio,
            drought_index, price_change_abs, farm_size_ha, has_insurance

    Returns:
        dict with risk_score, repayment_probability, debt_capacity_sek
    """
    models = bundle["models"]
    risk = float(models["credit_risk_classifier"].predict_proba(features)[0, 1])
    repay = float(models["repayment_regressor"].predict(features)[0])
    capacity = float(models["debt_capacity_regressor"].predict(features)[0])

    return {
        "risk_score": round(risk, 4),
        "repayment_probability": round(repay, 4),
        "debt_capacity_sek": round(capacity, 2),
        "risk_level": "low" if risk < 0.3 else "medium" if risk < 0.5 else "high",
    }


# ---- Quick test ----
if __name__ == "__main__":
    bundle = load_model()
    print(f"Loaded: {bundle['version']} | {bundle['n_features']} features | 3 models")
    print(f"Features: {bundle['feature_names']}")

    # Test with sample feature vector (Erik Johansson-like)
    sample = np.array([[
        0.38,   # debt_to_income (38%)
        1.32,   # dscr
        0.82,   # working_capital_100k
        0.18,   # operating_margin
        0.45,   # loan_to_value
        2.20,   # asset_coverage
        1.80,   # current_ratio
        0.60,   # debt_to_equity
        0.15,   # cash_flow_margin
        2.50,   # interest_coverage
        0.95,   # repayment_ratio
        0.23,   # drought_index
        0.018,  # price_change_abs
        85.0,   # farm_size_ha
        1.0,    # has_insurance
    ]])

    result = predict(bundle, sample)
    print(f"\nSample prediction:")
    print(f"  Risk: {result['risk_score']:.1%}")
    print(f"  Repayment: {result['repayment_probability']:.1%}")
    print(f"  Capacity: {result['debt_capacity_sek']:,.0f} SEK")
    print(f"  Level: {result['risk_level']}")
