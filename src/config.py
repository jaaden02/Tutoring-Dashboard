"""Configuration module for Tutoring Dashboard application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_FILE)


class Config:
    """Base configuration."""

    # Google Sheets Configuration
    SERVICE_ACCOUNT_FILE = "keys.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SPREADSHEET_ID = os.getenv("SAMPLE_SPREADSHEET_ID", "")
    SHEET_RANGE = "Daten!A1:H"

    # Cache Configuration
    CACHE_TTL = 10  # seconds
    
    # Data Processing
    DATE_FORMAT = "%d.%m.%Y"
    TIME_FORMAT = "%H:%M"
    
    # App Configuration
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    PORT = int(os.getenv("PORT", 8050))
    HOST = os.getenv("HOST", "127.0.0.1")
    
    # Pagination
    PAGE_SIZE = 10
    
    # Chart Colors
    CHART_COLORS = ["#4682B4", "#5F9EA0", "#66CDAA"]
    PRIMARY_COLOR = "#4682B4"
    
    # Chart Configuration
    TOP_STUDENTS_COUNT = 10


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


def get_config():
    """Get configuration based on environment."""
    env = os.getenv("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
