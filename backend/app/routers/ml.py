"""
AgriSense ML Operations Router - model evaluation, retraining.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["ML Ops"])


@router.post("/ml/evaluate")
def run_deployment_evaluation(n_farmers: int = 1000, seed: int = 999):
    """Generate 1000 unseen farmers and evaluate model performance."""
    from ..services.evaluation import (
        generate_evaluation_set, run_batch_inference, compute_evaluation_metrics,
    )

    logger.info(f"Generating {n_farmers} eval farmers (seed={seed})...")
    farmers = generate_evaluation_set(n_farmers=n_farmers, seed=seed)

    logger.info(f"Running batch inference on {len(farmers)} farmers...")
    results = run_batch_inference(farmers)

    logger.info("Computing evaluation metrics...")
    metrics = compute_evaluation_metrics(results)

    # Save to disk
    import json
    from datetime import datetime
    from pathlib import Path
    eval_dir = Path("data/evaluations")
    eval_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(eval_dir / f"evaluation_{timestamp}.json", "w") as f:
        json.dump({"metrics": metrics, "n_samples": len(results)}, f, indent=2)

    return {
        "status": "complete",
        "n_farmers": len(results),
        "metrics": metrics,
        "saved_to": f"data/evaluations/evaluation_{timestamp}.json",
    }


@router.get("/ml/latest-evaluation")
def get_latest_evaluation():
    """Get the most recent evaluation results."""
    import json
    from pathlib import Path
    eval_dir = Path("data/evaluations")
    files = sorted(eval_dir.glob("eval_latest.json"), reverse=True)
    if not files:
        raise HTTPException(404, "No evaluation found. Run: python run_eval.py")
    with open(files[0]) as f:
        return json.load(f)

@router.get("/ml/evaluation")
def get_ml_evaluation():
    """Get the latest ML model evaluation metrics."""
    from ..services.feature_engineering import get_latest_evaluation

    eval_data = get_latest_evaluation()
    if not eval_data:
        raise HTTPException(404, "No evaluation data found. Run training first.")

    return eval_data


@router.post("/ml/retrain")
def retrain_models(db: Session = Depends(get_db)):
    """Retrain ML models with full pipeline (CV, grid search, evaluation)."""
    from ..services.ml_service import _train_from_database, _fit_and_save_models

    farmer_count = db.query(Farmer).count()
    if farmer_count < 10:
        raise HTTPException(400, f"Need at least 10 farmers, found {farmer_count}")

    logger.info(f"Retraining models on {farmer_count} farmers with full pipeline...")
    risk_model, repay_model, cap_model = _train_from_database(db, farmer_count, use_full_pipeline=True)

    return {
        "status": "retrained",
        "farmers_used": farmer_count,
        "message": "Models retrained with cross-validation, grid search, and full evaluation",
    }
