"""
External data service — integrates weather and commodity price APIs.
Falls back to mock data when API keys are not configured.
"""
import random
from datetime import date

import httpx

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)


async def fetch_weather_data(region: str = "Skane") -> dict:
    """
    Fetch weather data from OpenWeatherMap or return mock Swedish data.

    Returns dict with: rainfall_mm, temperature_celsius, drought_index, flood_risk
    """
    if settings.weather_api_available:
        try:
            async with httpx.AsyncClient() as client:
                # Skane, Sweden coordinates (55.5°N, 13.5°E)
                response = await client.get(
                    f"{settings.WEATHER_API_BASE_URL}/onecall",
                    params={
                        "lat": 55.47,
                        "lon": 13.45,
                        "appid": settings.WEATHER_API_KEY,
                        "units": "metric",
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    current = data.get("current", {})
                    daily = data.get("daily", [{}])[0]

                    rainfall = daily.get("rain", 0) or current.get("rain", {}).get("1h", 0)
                    temp = current.get("temp", 28)

                    logger.info(f"Weather API: {rainfall}mm, {temp}°C")
                    return {
                        "rainfall_mm": rainfall,
                        "temperature_celsius": temp,
                        "drought_index": max(0, 1 - (rainfall / 20)),
                        "flood_risk": "high" if rainfall > 50 else "medium" if rainfall > 20 else "low",
                        "source": "openweathermap",
                        "is_mock": False,
                    }
        except Exception as e:
            logger.warning(f"Weather API failed: {e}. Using mock data.")

    # Mock fallback — Swedish climate (Skane region)
    rainfall = round(random.uniform(500, 750), 1)
    temp = round(random.uniform(-2, 22), 1)  # Swedish annual range
    return {
        "rainfall_mm": rainfall,
        "temperature_celsius": temp,
        "drought_index": round(max(0, 1 - (rainfall / 15)), 2),
        "flood_risk": random.choice(["low", "low", "low"]),  # Skane is low flood risk
        "source": "mock_smhi",
        "is_mock": True,
    }


async def fetch_commodity_prices(commodity: str = "WHEAT") -> dict:
    """
    Fetch commodity prices from Alpha Vantage or return mock Swedish data.

    Returns dict with: commodity_name, price (SEK/kg), unit, price_change_pct
    """
    if settings.commodity_api_available:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.COMMODITY_API_BASE_URL,
                    params={
                        "function": "GLOBAL_QUOTE",
                        "symbol": commodity,
                        "apikey": settings.COMMODITY_API_KEY,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    quote = data.get("Global Quote", {})
                    if quote:
                        price = float(quote.get("05. price", 2200))
                        change_pct = float(quote.get("10. change percent", "0%").replace("%", ""))
                        logger.info(f"Commodity API: {commodity} = {price} SEK/kg")
                        return {
                            "commodity_name": commodity,
                            "commodity_price": price,
                            "price_unit": "SEK/kg",
                            "price_change_pct": change_pct,
                            "source": "alphavantage",
                            "is_mock": False,
                        }
        except Exception as e:
            logger.warning(f"Commodity API failed: {e}. Using mock data.")

    # Mock fallback — Swedish/EU commodity prices (SEK/kg, 2024 reference)
    mock_prices = {
        "WHEAT": (2.48, -1.8),
        "BARLEY": (2.10, 2.3),
        "OATS": (2.35, -0.5),
        "RAPESEED": (5.80, 4.1),
        "RYE": (1.95, 1.2),
    }
    price, change = mock_prices.get(commodity.upper(), (2.50, 1.0))
    return {
        "commodity_name": commodity,
        "commodity_price": price,
        "price_unit": "SEK/kg",
        "price_change_pct": change,
        "source": "mock_jordbruksverket",
        "is_mock": True,
    }


async def fetch_fuel_prices() -> dict:
    """Fetch current fuel prices (mock Swedish prices)."""
    return {
        "diesel_price": 22.50,    # SEK/L (Swedish agricultural diesel ~22-24 kr/L)
        "petrol_price": 19.85,    # SEK/L
        "fertilizer_urea": 420.0,  # SEK/100kg (NPK equivalent)
        "fertilizer_dap": 680.0,   # SEK/100kg
        "source": "mock_okq8",
        "is_mock": True,
    }


async def get_all_external_data(region: str = "Skane", commodity: str = "WHEAT") -> dict:
    """
    Fetch all external data concurrently.
    Returns a unified external data dictionary.
    """
    weather = await fetch_weather_data(region)
    commodity_data = await fetch_commodity_prices(commodity)
    fuel = await fetch_fuel_prices()

    return {
        "weather": weather,
        "commodity": commodity_data,
        "fuel": fuel,
        "government_subsidies": {
            "eu_cap_direct": 115000.0,    # EU CAP direct payment (SEK/yr, ~230 EUR/ha × 50ha)
            "greening_payment": 32000.0,   # CAP greening component
            "source": "mock_jordbruksverket",
        },
    }
