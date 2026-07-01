"""
Peer Benchmarking Engine

Compares a farmer against similar farms in the portfolio.
Decision-support layer - NOT fed into the ML model.

Filters peers by: region, crop type, farm size range.
Computes percentiles for key financial and operational metrics.
"""
import numpy as np
from sqlalchemy.orm import Session

from ..models import Farmer, FinancialRecord, ExistingLoan, OperationalData
from .financial_analysis import calculate_financial_ratios
from ..logger import get_logger

logger = get_logger(__name__)

# Regions in the synthetic portfolio (12 län, 30 municipalities)
COVERED_REGIONS = {
    "Skane": ["Skurup", "Lund", "Kristianstad", "Trelleborg", "Ystad", "Sjobo"],
    "Vastra Gotaland": ["Skovde", "Lidkoping", "Falkoping", "Vanersborg"],
    "Ostergotland": ["Linkoping", "Motala", "Mjolby", "Vadstena"],
    "Uppsala": ["Enkoping", "Tierp", "Osthammar"],
    "Sodermanland": ["Eskilstuna", "Nykoping", "Flen"],
    "Orebro": ["Kumla", "Hallsberg"],
    "Stockholm": ["Norrtalje", "Sodertalje"],
    "Kalmar": ["Vastervik", "Oskarshamn"],
    "Halland": ["Falkenberg", "Varberg"],
    "Gotland": ["Visby"],
    "Vastmanland": ["Vasteras"],
}


def _crop_family(crop_type: str) -> str:
    """Group crops into families for meaningful peer comparison."""
    c = (crop_type or "").lower()
    if "vete" in c or "wheat" in c:
        return "wheat"
    if "korn" in c or "barley" in c:
        return "barley"
    if "raps" in c or "rapeseed" in c:
        return "rapeseed"
    if "havre" in c or "oats" in c:
        return "oats"
    return "mixed"


def _percentile(values: list[float], target: float, higher_is_better: bool = True) -> tuple:
    """
    Calculate percentile rank of target within values.
    Returns (percentile 0-100, median, better_than_pct).
    """
    if not values or len(values) < 3:
        return 50, target, 50

    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 3:
        return 50, target, 50

    median = float(np.median(arr))

    if higher_is_better:
        pct = round(np.sum(arr <= target) / len(arr) * 100, 1)
    else:
        pct = round(np.sum(arr >= target) / len(arr) * 100, 1)

    return pct, median, round(pct)


def run_peer_benchmark(farmer_id: int, db: Session) -> dict:
    """
    Compare a farmer against peers with similar characteristics.

    Peer filters: same region (län), same crop family, farm size ±30%.
    """
    # Get target farmer
    farmer = db.get(Farmer, farmer_id)
    if not farmer:
        return {"error": "Farmer not found"}

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )

    if not financials or not ops:
        return {"error": "Insufficient data for benchmarking"}

    # Target metrics
    target_ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__,
    )

    target_crop = ops.crop_type or ""
    target_family = _crop_family(target_crop)
    target_region = farmer.state or ""
    target_size = ops.farm_size_acres or 0
    size_min = target_size * 0.70
    size_max = target_size * 1.30

    # Find peers
    all_farmers = db.query(Farmer).filter(
        Farmer.id != farmer_id,
        Farmer.state == target_region,
    ).all()

    peer_metrics = {
        "revenue": [], "net_income": [], "debt_to_income": [], "dscr": [],
        "operating_margin": [], "loan_to_value": [], "working_capital": [],
        "yield_per_ha": [], "cash_flow": [], "farm_size": [],
    }

    peer_count = 0
    for peer in all_farmers:
        peer_ops = (
            db.query(OperationalData)
            .filter(OperationalData.farmer_id == peer.id)
            .first()
        )
        if not peer_ops:
            continue

        peer_size = peer_ops.farm_size_acres or 0
        if peer_size < size_min or peer_size > size_max:
            continue

        peer_crop = peer_ops.crop_type or ""
        if _crop_family(peer_crop) != target_family:
            continue

        peer_fin = (
            db.query(FinancialRecord)
            .filter(FinancialRecord.farmer_id == peer.id)
            .order_by(FinancialRecord.year.desc())
            .first()
        )
        peer_loans = (
            db.query(ExistingLoan)
            .filter(ExistingLoan.farmer_id == peer.id)
            .all()
        )

        if not peer_fin:
            continue

        peer_ratios = calculate_financial_ratios(
            [peer_fin.__dict__],
            [l.__dict__ for l in peer_loans],
        )

        peer_metrics["revenue"].append(peer_fin.revenue or 0)
        peer_metrics["net_income"].append(peer_fin.net_income or 0)
        peer_metrics["debt_to_income"].append(peer_ratios.get("debt_to_income", 0))
        peer_metrics["dscr"].append(peer_ratios.get("dscr", 1))
        peer_metrics["operating_margin"].append(peer_ratios.get("operating_margin", 0))
        peer_metrics["loan_to_value"].append(peer_ratios.get("loan_to_value", 0))
        peer_metrics["working_capital"].append(peer_ratios.get("working_capital", 0))

        if peer_size > 0:
            peer_metrics["yield_per_ha"].append(
                (peer_ops.crop_yield_kg or 0) / peer_size
            )
        peer_metrics["cash_flow"].append(peer_fin.operating_cash_flow or 0)
        peer_metrics["farm_size"].append(peer_size)
        peer_count += 1

    if peer_count < 3:
        return {
            "error": f"Only {peer_count} peers found. Need at least 3 for meaningful comparison.",
            "peer_count": peer_count,
            "filters": {
                "region": target_region,
                "crop_family": target_family,
                "farm_size_range": f"{size_min:.0f}-{size_max:.0f} ha",
            },
        }

    # Target values
    targets = {
        "revenue": financials[0].revenue or 0,
        "net_income": financials[0].net_income or 0,
        "debt_to_income": target_ratios.get("debt_to_income", 0),
        "dscr": target_ratios.get("dscr", 1),
        "operating_margin": target_ratios.get("operating_margin", 0),
        "loan_to_value": target_ratios.get("loan_to_value", 0),
        "working_capital": target_ratios.get("working_capital", 0),
        "yield_per_ha": (ops.crop_yield_kg or 0) / max(target_size, 1),
        "cash_flow": financials[0].operating_cash_flow or 0,
        "farm_size": target_size,
    }

    # Higher = better for these
    higher_better = {
        "revenue": True, "net_income": True, "dscr": True,
        "operating_margin": True, "working_capital": True,
        "yield_per_ha": True, "cash_flow": True,
        "debt_to_income": False, "loan_to_value": False,
        "farm_size": True,
    }

    # Compute percentiles
    benchmarks = {}
    for metric, values in peer_metrics.items():
        if len(values) < 3:
            continue
        target_val = targets.get(metric, 0)
        is_higher_better = higher_better.get(metric, True)
        pct, median, rank = _percentile(values, target_val, is_higher_better)

        # Interpretation
        if rank >= 80:
            interpretation = _top_interpretation(metric, is_higher_better)
        elif rank >= 60:
            interpretation = "Above average"
        elif rank >= 40:
            interpretation = "Average - comparable to peers"
        elif rank >= 20:
            interpretation = "Below average"
        else:
            interpretation = _bottom_interpretation(metric, is_higher_better)

        benchmarks[metric] = {
            "label": _metric_label(metric),
            "value": round(target_val, 2),
            "peer_median": round(median, 2),
            "percentile": rank,
            "better_than_pct": rank if is_higher_better else (100 - rank),
            "interpretation": interpretation,
            "higher_is_better": is_higher_better,
        }

    # Overall peer position
    all_ranks = [b["better_than_pct"] for b in benchmarks.values()]
    overall_position = round(np.mean(all_ranks), 1) if all_ranks else 50

    logger.info(f"Peer benchmark for farmer {farmer_id}: {peer_count} peers, "
                f"overall position: {overall_position}th percentile")

    return {
        "farmer_id": farmer_id,
        "farmer_name": farmer.full_name,
        "peer_count": peer_count,
        "filters_applied": {
            "region": target_region,
            "crop_family": target_family,
            "farm_size_range": f"{size_min:.0f}–{size_max:.0f} ha",
        },
        "overall_percentile": overall_position,
        "overall_interpretation": (
            f"Stronger than {overall_position:.0f}% of similar farms"
            if overall_position > 55 else
            f"Comparable to peers (middle {overall_position:.0f}%)"
            if overall_position >= 45 else
            f"Weaker than {100 - overall_position:.0f}% of similar farms"
        ),
        "benchmarks": benchmarks,
    }


def _metric_label(metric: str) -> str:
    labels = {
        "revenue": "Revenue",
        "net_income": "Net Income",
        "debt_to_income": "Debt-to-Income",
        "dscr": "DSCR",
        "operating_margin": "Operating Margin",
        "loan_to_value": "Loan-to-Value",
        "working_capital": "Working Capital",
        "yield_per_ha": "Yield (kg/ha)",
        "cash_flow": "Operating Cash Flow",
        "farm_size": "Farm Size",
    }
    return labels.get(metric, metric)


def _top_interpretation(metric: str, higher_better: bool) -> str:
    if not higher_better:
        return "Low - favorable position" if metric in ("debt_to_income", "loan_to_value") else "Strong position"
    return "Top performer among peers"


def _bottom_interpretation(metric: str, higher_better: bool) -> str:
    if not higher_better:
        return "High - potential concern" if metric in ("debt_to_income", "loan_to_value") else "Below peers"
    return "Significantly below peers - review recommended"
