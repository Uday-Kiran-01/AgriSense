from backend.app.services.evaluation import generate_evaluation_set, run_batch_inference, compute_evaluation_metrics, compute_threshold_curve

print("Generating 1000 eval farmers (seed=999, shifted distributions)...")
farmers = generate_evaluation_set(n_farmers=1000, seed=999)
print("Running batch inference...")
results = run_batch_inference(farmers)
print("Computing metrics...")
metrics = compute_evaluation_metrics(results)
curve = compute_threshold_curve(results)
m = metrics["metrics"]

print("=" * 55)
print("MODEL EVALUATION - 1,000 Unseen Farmers")
print("(Different seed, shifted distributions from training)")
print("=" * 55)
print("Accuracy:  ", round(m['accuracy'] * 100, 1), "%")
print("Precision: ", round(m['precision'] * 100, 1), "%")
print("Recall:    ", round(m['recall'] * 100, 1), "%")
print("F1 Score:  ", round(m['f1_score'], 3))
print("ROC-AUC:   ", round(m['roc_auc'], 3))
print("TP:", m["true_positives"], "FP:", m["false_positives"])
print("FN:", m["false_negatives"], "TN:", m["true_negatives"])
print()

print("PRECISION-RECALL TRADE-OFF BY THRESHOLD")
print("Thr  | Precision | Recall   | F1    | Reviews | Business Impact")
print("-" * 70)
for c in curve["curve"]:
    t = c["threshold"]
    if t in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
        print("{:.2f} | {:.1%}     | {:.1%}    | {:.3f} | {:4d}   | {}".format(
            t, c['precision'], c['recall'], c['f1'], c['manual_reviews'],
            c['interpretation'][:50]))

print()
print("Caveat: Synthetic evaluation data. Not production lending performance.")
print("All recommendations are advisory. Final decisions by human loan officers.")
