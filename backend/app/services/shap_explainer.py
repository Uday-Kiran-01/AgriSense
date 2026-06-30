"""
SHAP Explainability (Optional — requires `pip install shap`)

Provides per-prediction explanations: WHY did THIS specific farmer
get THIS specific risk score?

Unlike feature importance (which shows global importance),
SHAP shows the contribution of each feature to a single prediction.

Usage:
  1. pip install shap
  2. Uncomment the code below
  3. Call GET /api/farmers/{id}/shap-explanation
"""
import json
import numpy as np

from ..logger import get_logger

logger = get_logger(__name__)

# --- Uncomment after `pip install shap` ---
# import shap


def generate_shap_explanation(model, features: np.ndarray,
                               feature_names: list[str]) -> dict | None:
    """
    Generate SHAP values for a single prediction.

    Returns per-feature contribution to the prediction.
    Requires: pip install shap
    """
    try:
        import shap
    except ImportError:
        logger.warning("SHAP not installed. Run: pip install shap")
        return {
            "status": "unavailable",
            "message": "SHAP not installed. Run: pip install shap for per-prediction explanations.",
            "fallback": "Feature importance from Random Forest is available instead.",
        }

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(features)

        # For binary classifier, shap_values is a list [class_0, class_1]
        if isinstance(shap_values, list):
            shap_vals = shap_values[1][0]  # class 1 (high risk)
        else:
            shap_vals = shap_values[0]

        # Pair feature names with SHAP values
        contributions = []
        for name, val in zip(feature_names, shap_vals):
            contributions.append({
                "feature": name,
                "shap_value": round(float(val), 6),
                "direction": "increases_risk" if val > 0 else "decreases_risk",
            })

        # Sort by absolute impact
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        # Expected value (base prediction before any features)
        if isinstance(explainer.expected_value, list):
            base_value = float(explainer.expected_value[1])
        else:
            base_value = float(explainer.expected_value)

        logger.info(f"SHAP explanation generated: {len(contributions)} features, "
                    f"base_value={base_value:.3f}")

        return {
            "status": "available",
            "base_value": round(base_value, 4),
            "base_value_interpretation": (
                "Average model prediction before considering any farmer-specific features. "
                f"A base value of {base_value:.2%} means the average farmer has "
                f"a {base_value:.0%} risk of default."
            ),
            "top_risk_increasers": [c for c in contributions if c["shap_value"] > 0][:5],
            "top_risk_decreasers": [c for c in contributions if c["shap_value"] < 0][:5],
            "all_contributions": contributions,
            "waterfall_summary": (
                f"Base risk: {base_value:.2%} → "
                f"Final risk: {base_value + sum(c['shap_value'] for c in contributions):.2%}"
            ),
        }
    except Exception as e:
        logger.error(f"SHAP explanation failed: {e}")
        return {"status": "error", "message": str(e)}
