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


async def fetch_weather_data(region: str = "Gujarat") -> dict:
    """
    Fetch weather data from OpenWeatherMap or return mock data.

    Returns dict with: rainfall_mm, temperature_celsius, drought_index, flood_risk
    """
    if settings.weather_api_available:
        try:
            async with httpx.AsyncClient() as client:
                # Using One Call API 3.0 (requires lat/lon — using mock coords for Gujarat)
                response = await client.get(
                    f"{settings.WEATHER_API_BASE_URL}/onecall",
                    params={
                        "lat": 22.2587,
                        "lon": 71.1924,
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

    # Mock fallback
    rainfall = round(random.uniform(600, 1200), 1)
    return {
        "rainfall_mm": rainfall,
        "temperature_celsius": round(random.uniform(25, 35), 1),
        "drought_index": round(max(0, 1 - (rainfall / 20)), 2),
        "flood_risk": random.choice(["low", "low", "medium"]),
        "source": "mock",
        "is_mock": True,
    }


async def fetch_commodity_prices(commodity: str = "WHEAT") -> dict:
    """
    Fetch commodity prices from Alpha Vantage or return mock data.

    Returns dict with: commodity_name, price, unit, price_change_pct
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
                        logger.info(f"Commodity API: {commodity} = ₹{price}")
                        return {
                            "commodity_name": commodity,
                            "commodity_price": price,
                            "price_unit": "INR/quintal",
                            "price_change_pct": change_pct,
                            "source": "alphavantage",
                            "is_mock": False,
                        }
        except Exception as e:
            logger.warning(f"Commodity API failed: {e}. Using mock data.")

    # Mock fallback — realistic Indian commodity prices
    mock_prices = {
        "WHEAT": (2275, 3.2),
        "RICE": (3200, -1.5),
        "MAIZE": (1850, 5.1),
        "SUGARCANE": (315, 0.8),
        "COTTON": (6200, -2.3),
    }
    price, change = mock_prices.get(commodity.upper(), (2200, 1.0))
    return {
        "commodity_name": commodity,
        "commodity_price": price,
        "price_unit": "INR/quintal",
        "price_change_pct": change,
        "source": "mock",
        "is_mock": True,
    }


async def fetch_fuel_prices() -> dict:
    """Fetch current fuel prices (mock always for demo)."""
    return {
        "diesel_price": 92.50,
        "petrol_price": 104.75,
        "fertilizer_urea": 265.0,
        "fertilizer_dap": 1350.0,
        "source": "mock",
        "is_mock": True,
    }


async def get_all_external_data(region: str = "Gujarat", commodity: str = "WHEAT") -> dict:
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
            "pm_kisan": 6000.0,
            "fertilizer_subsidy": 4500.0,
            "source": "mock",
        },
    }
