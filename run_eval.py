"""Run full evaluation on 1000 farmers and save individual predictions."""
import json, datetime
from pathlib import Path
from backend.app.services.evaluation import generate_evaluation_set, run_batch_inference, compute_evaluation_metrics

print("Generating 1,000 eval farmers (seed=999)...")
farmers = generate_evaluation_set(n_farmers=1000, seed=999)

print("Running batch inference (this takes ~2 min)...")
results = run_batch_inference(farmers)

print("Computing metrics...")
metrics = compute_evaluation_metrics(results)
m = metrics["metrics"]

print(f"\nDone! {len(results)} farmers evaluated.")
print(f"Accuracy:  {m['accuracy']:.1%}")
print(f"Precision: {m['precision']:.1%}")
print(f"Recall:    {m['recall']:.1%}")
print(f"F1:        {m['f1_score']:.3f}")
print(f"ROC-AUC:   {m['roc_auc']:.3f}")
print(f"TP={m['true_positives']} FP={m['false_positives']} FN={m['false_negatives']} TN={m['true_negatives']}")

# Save individual predictions for threshold slider
eval_dir = Path("data/evaluations")
eval_dir.mkdir(parents=True, exist_ok=True)

individuals = []
for r in results:
    individuals.append({
        "name": str(r.get("farmer_name", "")),
        "profile": str(r.get("profile", "")),
        "actual_high_risk": bool(r.get("actual_high_risk", False)),
        "predicted_risk_score": float(r.get("predicted_risk_score", 0)),
        "predicted_repay_prob": float(r.get("predicted_repay_prob", 0)),
        "recommendation": str(r.get("recommendation", "")),
        "dti": float(r.get("dti", 0)),
        "dscr": float(r.get("dscr", 0)),
        "liquidity_status": str(r.get("liquidity_status", "")),
        "negative_months": int(r.get("negative_months", 0)),
        "has_insurance": bool(r.get("has_insurance", False)),
    })

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data = {
    "evaluation_date": ts,
    "n_farmers": len(results),
    "seed": 999,
    "note": "Different seed and shifted distributions from training (seed=42).",
    "metrics": metrics,
    "individual_predictions": individuals,
}

with open(eval_dir / f"eval_full_{ts}.json", "w") as f:
    json.dump(data, f, indent=2, default=str)

with open(eval_dir / "eval_latest.json", "w") as f:
    json.dump(data, f, indent=2, default=str)

print(f"\nSaved: data/evaluations/eval_full_{ts}.json")
print("Ready for threshold slider!")
