"""
AgriSense AI Configuration
Loads settings from .env file with sensible defaults.
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

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Weather API
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_BASE_URL: str = os.getenv(
        "WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/3.0"
    )

    # Commodity API
    COMMODITY_API_KEY: str = os.getenv("COMMODITY_API_KEY", "")
    COMMODITY_API_BASE_URL: str = os.getenv(
        "COMMODITY_API_BASE_URL", "https://www.alphavantage.co/query"
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

    @property
    def weather_api_available(self) -> bool:
        """Check if weather API key is configured."""
        return bool(self.WEATHER_API_KEY) and self.WEATHER_API_KEY != "your_openweathermap_api_key_here"

    @property
    def commodity_api_available(self) -> bool:
        """Check if commodity API key is configured."""
        return bool(self.COMMODITY_API_KEY) and self.COMMODITY_API_KEY != "your_alphavantage_api_key_here"


settings = Settings()
