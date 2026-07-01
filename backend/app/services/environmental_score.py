"""
Environmental Risk Score - composite score from weather, commodity, and fuel data.
"""
from ..logger import get_logger

logger = get_logger(__name__)


def calculate_environmental_score(weather: dict, commodity: dict, fuel: dict) -> dict:
    """
    Calculate composite environmental risk score (0-100, lower is better).

    Components:
    - Weather risk (drought, flood)
    - Commodity price risk (volatility)
    - Input cost risk (fuel, fertilizer)
    """
    score = 0
    breakdown = {}

    # 1. Weather risk (0-40 points)
    drought = weather.get("drought_index", 0.3)
    flood = weather.get("flood_risk", "low")

    weather_score = 0
    if drought > 0.5:
        weather_score += 25
    elif drought > 0.3:
        weather_score += 15
    elif drought > 0.15:
        weather_score += 8
    else:
        weather_score += 3

    if flood == "high":
        weather_score += 15
    elif flood == "medium":
        weather_score += 8
    else:
        weather_score += 2

    score += min(40, weather_score)
    breakdown["weather"] = {
        "score": min(40, weather_score),
        "max": 40,
        "details": f"Drought index {drought:.2f}, flood risk: {flood}",
    }

    # 2. Commodity price risk (0-30 points)
    price_change = abs(commodity.get("price_change_pct", 2))
    commodity_score = 0
    if price_change > 10:
        commodity_score += 25
    elif price_change > 5:
        commodity_score += 15
    elif price_change > 2:
        commodity_score += 8
    else:
        commodity_score += 3

    score += min(30, commodity_score)
    breakdown["commodity"] = {
        "score": min(30, commodity_score),
        "max": 30,
        "details": f"Price volatility: {price_change:.1f}%",
    }

    # 3. Input cost risk (0-30 points)
    diesel = fuel.get("diesel_price", 22)
    fertilizer = fuel.get("fertilizer_dap", 680)
    input_score = 0
    if diesel > 28:
        input_score += 15
    elif diesel > 24:
        input_score += 10
    elif diesel > 20:
        input_score += 5
    else:
        input_score += 2

    if fertilizer > 800:
        input_score += 15
    elif fertilizer > 650:
        input_score += 8
    else:
        input_score += 2

    score += min(30, input_score)
    breakdown["input_costs"] = {
        "score": min(30, input_score),
        "max": 30,
        "details": f"Diesel {diesel:.2f} kr/L, fertilizer {fertilizer:.0f} kr/tonne",
    }

    total = min(100, score)
    risk_level = "low" if total <= 25 else "medium" if total <= 55 else "high"

    logger.info(f"Environmental risk score: {total}/100 ({risk_level})")

    return {
        "total_score": total,
        "risk_level": risk_level,
        "breakdown": breakdown,
        "sources": {
            "weather": weather.get("source", "mock"),
            "commodity": commodity.get("source", "mock"),
            "fuel": fuel.get("source", "mock"),
        },
    }
