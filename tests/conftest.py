"""Fixtures for testing."""
import pandas as pd
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_data():
    """Create sample tutoring data for testing."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    return pd.DataFrame({
        "Datum:": [
            yesterday.strftime("%d.%m.%Y"),
            (yesterday - timedelta(days=1)).strftime("%d.%m.%Y"),
            (yesterday - timedelta(days=7)).strftime("%d.%m.%Y"),
        ],
        "Name:": ["Alice", "Bob", "Alice"],
        "Anfang:": ["10:00", "14:00", "11:00"],
        "Ende:": ["11:30", "15:30", "12:30"],
        "Anbieter:": ["School A", "School B", "School A"],
        "Stunden:": ["1.5", "1.5", "1.5"],
        "Lohn:": ["30,00", "30,00", "30,00"],
    })


@pytest.fixture
def config():
    """Create test configuration."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    
    from src.config import Config
    
    config = Config()
    config.CACHE_TTL = 0.1  # Very short for testing
    config.SERVICE_ACCOUNT_FILE = "tests/fixtures/mock_keys.json"
    return config


@pytest.fixture
def mock_google_sheets_data():
    """Mock data that would come from Google Sheets API."""
    today = datetime.now()
    return [
        [
            "Datum:",
            "Name:",
            "Anfang:",
            "Ende:",
            "Anbieter:",
            "Stunden:",
            "Lohn:",
        ],  # Headers
        [
            (today - timedelta(days=1)).strftime("%d.%m.%Y"),
            "Alice",
            "10:00",
            "11:30",
            "School A",
            "1.5",
            "30,00",
        ],
        [
            (today - timedelta(days=2)).strftime("%d.%m.%Y"),
            "Bob",
            "14:00",
            "15:30",
            "School B",
            "1.5",
            "30,00",
        ],
        [
            (today - timedelta(days=7)).strftime("%d.%m.%Y"),
            "Alice",
            "11:00",
            "12:30",
            "School A",
            "1.5",
            "30,00",
        ],
    ]
