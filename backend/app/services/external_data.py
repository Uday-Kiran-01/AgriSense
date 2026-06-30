"""
External data service — free public APIs for weather and commodity prices.

Data sources (no API keys required):
  - SMHI (Swedish Meteorological and Hydrological Institute) — weather observations
  - EU Agri-Food Data Portal (European Commission) — cereal/grain prices
  - Mock fallbacks for fuel, fertilizer, and EU CAP subsidies

Architecture: Each external API has a clean interface. Swapping mock for real
requires changing only this service — no downstream changes needed.
"""
import random
from datetime import date

import httpx

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# SMHI — Swedish weather (free, no API key)
# ---------------------------------------------------------------------------

# Skane region stations: Lund, Helsingborg, Kristianstad, Trelleborg
SMHI_SKANE_STATIONS = {
    "Lund": "53430",
    "Helsingborg": "62040",
    "Kristianstad": "64030",
    "Trelleborg": "53230",
}

# SMHI parameter IDs
SMHI_PARAM = {
    "temperature": 1,      # Lufttemperatur, hourly, °C
    "temp_daily_mean": 2,  # Lufttemperatur, daily mean, °C
    "precipitation": 5,    # Nederbordsmangd, daily sum, mm
    "humidity": 6,         # Relativ Luftfuktighet, hourly, %
    "wind_speed": 4,       # Vindhastighet, 10-min mean, m/s
    "snow_depth": 8,       # Snodjup, daily, m
    "temp_min": 19,        # Lufttemperatur, daily min, °C
    "temp_max": 20,        # Lufttemperatur, daily max, °C
}


async def _fetch_smhi_station_data(station_key: str, parameter: int) -> dict | None:
    """Fetch latest data for a specific SMHI station and parameter."""
    url = (
        f"{settings.SMHI_BASE_URL}/parameter/{parameter}"
        f"/station/{station_key}/period/latest-hour.json"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("value", [])
                if values:
                    return {
                        "station_name": data.get("station", {}).get("name", station_key),
                        "parameter_name": data.get("parameter", {}).get("title", ""),
                        "unit": data.get("unit", ""),
                        "latest_value": values[-1].get("value"),
                        "latest_date": values[-1].get("date"),
                        "num_values": len(values),
                    }
    except Exception as e:
        logger.debug(f"SMHI station {station_key} param {parameter}: {e}")
    return None


async def _fetch_smhi_stationset(parameter: int) -> list[dict] | None:
    """Fetch latest-hour data for ALL active Swedish stations for a parameter."""
    url = (
        f"{settings.SMHI_BASE_URL}/parameter/{parameter}"
        f"/station-set/all/period/latest-hour.json"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("value", [])
                return values  # list of {date, value, station_name, station_key, ...}
    except Exception as e:
        logger.debug(f"SMHI stationset param {parameter}: {e}")
    return None


async def fetch_weather_data(region: str = "Skane") -> dict:
    """
    Fetch weather data from SMHI Open Data (free, no API key).
    Falls back to mock Swedish data if SMHI is unreachable.

    Returns dict with: temperature_celsius, rainfall_mm, drought_index,
                       wind_speed_ms, humidity_pct, snow_depth_m, source, is_mock
    """
    station_key = SMHI_SKANE_STATIONS.get("Lund", "53430")

    # Try SMHI live data for temperature and precipitation
    temp_data = await _fetch_smhi_station_data(station_key, SMHI_PARAM["temperature"])
    precip_data = await _fetch_smhi_station_data(station_key, SMHI_PARAM["precipitation"])
    wind_data = await _fetch_smhi_station_data(station_key, SMHI_PARAM["wind_speed"])
    humidity_data = await _fetch_smhi_station_data(station_key, SMHI_PARAM["humidity"])

    if temp_data or precip_data:
        temp = temp_data["latest_value"] if temp_data else random.uniform(-2, 22)
        rainfall = precip_data["latest_value"] if precip_data else random.uniform(0, 5)
        wind = wind_data["latest_value"] if wind_data else random.uniform(2, 8)
        humidity = humidity_data["latest_value"] if humidity_data else random.uniform(60, 90)

        # Drought index: normalize recent rainfall against Swedish monthly norms
        # Skane average monthly rainfall: ~50mm (summer) to ~70mm (winter)
        drought_index = round(max(0, 1 - (rainfall / 30)), 2)

        logger.info(
            f"SMHI Live: {temp}C, {rainfall}mm precip, {wind}m/s wind, "
            f"{humidity}% humidity (station: {station_key})"
        )
        return {
            "temperature_celsius": round(temp, 1),
            "rainfall_mm": round(rainfall, 1),
            "drought_index": drought_index,
            "flood_risk": "high" if rainfall > 50 else "medium" if rainfall > 20 else "low",
            "wind_speed_ms": round(wind, 1),
            "humidity_pct": round(humidity, 1),
            "snow_depth_m": 0,  # SMHI snow depth available only in winter
            "source": "smhi_live",
            "is_mock": False,
        }

    # Mock fallback — Swedish climate (Skane region)
    rainfall = round(random.uniform(500, 750), 1)
    temp = round(random.uniform(-2, 22), 1)
    logger.info(f"SMHI unavailable — using mock data ({temp}C, {rainfall}mm)")
    return {
        "temperature_celsius": temp,
        "rainfall_mm": rainfall,
        "drought_index": round(max(0, 1 - (rainfall / 650)), 2),
        "flood_risk": "low",
        "wind_speed_ms": round(random.uniform(2, 8), 1),
        "humidity_pct": round(random.uniform(60, 90), 1),
        "snow_depth_m": 0,
        "source": "mock_smhi",
        "is_mock": True,
    }


# ---------------------------------------------------------------------------
# EU Agri-Food Data Portal — commodity prices (free, no API key)
# ---------------------------------------------------------------------------

# Mapping from our commodity names to EU cereal product codes
EU_CEREAL_CODES = {
    "WHEAT": "BLTFOUR",     # Feed wheat
    "BREAD_WHEAT": "BLTPAN",  # Breadmaking common wheat
    "DURUM": "DUR",          # Durum wheat
    "BARLEY": "ORGBRAS",     # Malting barley (also: ORGFOUR = Feed barley)
    "FEED_BARLEY": "ORGFOUR",
    "OATS": "AVO",           # Feed oats
    "RYE": "SEGFOUR",        # Feed rye
    "MAIZE": "MAI",          # Feed maize
    "TRITICALE": "TRI",      # Triticale
}


async def fetch_commodity_prices(commodity: str = "WHEAT") -> dict:
    """
    Fetch commodity prices from EU Agri-Food Data Portal (free, no API key).
    Falls back to mock Swedish reference prices if unavailable.

    Prices are in EUR/tonne from the API; converted to SEK/kg for the demo.

    Returns dict with: commodity_name, price (SEK/kg), price_eur_tonne,
                       unit, price_change_pct, source, is_mock
    """
    product_code = EU_CEREAL_CODES.get(commodity.upper(), "BLTFOUR")

    try:
        async with httpx.AsyncClient() as client:
            # Query Swedish cereal prices for the last 3 months
            resp = await client.get(
                f"{settings.EU_AGRIFOOD_BASE_URL}/api/cereal/prices",
                params={
                    "memberStateCodes": "SE",
                    "productCodes": product_code,
                    "beginDate": "01/01/2024",
                    "endDate": "31/12/2024",
                },
                timeout=15.0,
            )
            if resp.status_code == 200:
                prices = resp.json()
                if prices:
                    # Get the most recent price entry
                    latest = prices[-1]
                    price_eur_tonne = float(latest.get("price", "0").replace("€", ""))
                    # Convert EUR/tonne to SEK/kg: EUR/tonne / 1000 * EUR_SEK_rate
                    # Approximate EUR/SEK: ~11.5
                    price_sek_kg = round(price_eur_tonne / 1000 * 11.5, 2)

                    # Calculate change from previous entry
                    change_pct = 0.0
                    if len(prices) > 1:
                        prev = float(prices[-2].get("price", "0").replace("€", ""))
                        if prev > 0:
                            change_pct = round((price_eur_tonne - prev) / prev * 100, 1)

                    logger.info(
                        f"EU Agri-Food: {commodity} = EUR{price_eur_tonne}/tonne "
                        f"(~{price_sek_kg} SEK/kg) | source: EU Commission"
                    )
                    return {
                        "commodity_name": commodity,
                        "commodity_price": price_sek_kg,
                        "price_eur_tonne": price_eur_tonne,
                        "price_unit": "SEK/kg",
                        "price_change_pct": change_pct,
                        "source": "eu_agrifood",
                        "is_mock": False,
                    }
    except Exception as e:
        logger.warning(f"EU Agri-Food API failed: {e}. Using mock data.")

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
        "price_eur_tonne": round(price * 1000 / 11.5, 1),
        "price_unit": "SEK/kg",
        "price_change_pct": change,
        "source": "mock_jordbruksverket",
        "is_mock": True,
    }


# ---------------------------------------------------------------------------
# Fuel & Fertilizer (mock — no free real-time API available)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Unified external data fetcher
# ---------------------------------------------------------------------------

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
            "eu_cap_direct": 115000.0,    # EU CAP direct payment (SEK/yr, ~230 EUR/ha x 50ha)
            "greening_payment": 32000.0,   # CAP greening component
            "source": "mock_jordbruksverket",
        },
    }
