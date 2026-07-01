"""
AgriSense AI Configuration
Loads settings from .env file with sensible defaults.

External data sources are FREE and PUBLIC - no API keys required:
  - SMHI (Swedish Meteorological and Hydrological Institute) - weather
  - EU Agri-Food Data Portal (European Commission) - commodity prices
  - Gemini AI (Google) - decision memo generation (optional)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'agrisense.db'}"
    )

    # Gemini AI (optional - falls back to rule-based if not configured)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # ---- Free Public APIs ----

    # SMHI Open Data - Swedish weather (no API key required)
    SMHI_BASE_URL: str = os.getenv(
        "SMHI_BASE_URL",
        "https://opendata-download-metobs.smhi.se/api/version/1.0",
    )

    # EU Agri-Food Data Portal - commodity prices (no API key required)
    EU_AGRIFOOD_BASE_URL: str = os.getenv(
        "EU_AGRIFOOD_BASE_URL",
        "https://api.tech.ec.europa.eu/agrifood",
    )

    # FAOSTAT (UN FAO) - crop production, yield, producer prices (no API key required)
    FAOSTAT_BASE_URL: str = os.getenv(
        "FAOSTAT_BASE_URL",
        "https://fenixservices.fao.org/faostat/api/v2/en",
    )

    # Eurostat - EU agricultural price indices (no API key required)
    EUROSTAT_BASE_URL: str = os.getenv(
        "EUROSTAT_BASE_URL",
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data",
    )

    # App
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MODEL_PATH: str = os.getenv("MODEL_PATH", str(BASE_DIR / "data" / "models"))
    SAMPLE_DATA_PATH: str = os.getenv(
        "SAMPLE_DATA_PATH", str(BASE_DIR / "data" / "samples")
    )

    # Hugging Face
    HF_USERNAME: str = os.getenv("HF_USERNAME", "")
    HF_SPACE_NAME: str = os.getenv("HF_SPACE_NAME", "agrisense-ai")

    @property
    def gemini_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.GEMINI_API_KEY) and self.GEMINI_API_KEY != "your_gemini_api_key_here"


settings = Settings()
