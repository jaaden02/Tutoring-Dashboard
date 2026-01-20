"""Tests for config module."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import Config, DevelopmentConfig, ProductionConfig, get_config


class TestConfig:
    """Test cases for configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.SERVICE_ACCOUNT_FILE == "keys.json"
        assert config.SCOPES == ["https://www.googleapis.com/auth/spreadsheets"]
        assert config.CACHE_TTL == 10
        assert config.DATE_FORMAT == "%d.%m.%Y"
        assert config.TIME_FORMAT == "%H:%M"
        assert config.PAGE_SIZE == 10
        assert config.TOP_STUDENTS_COUNT == 10

    def test_development_config(self):
        """Test development configuration."""
        config = DevelopmentConfig()
        assert config.DEBUG is True

    def test_production_config(self):
        """Test production configuration."""
        config = ProductionConfig()
        assert config.DEBUG is False

    def test_get_config_development(self):
        """Test get_config returns development config by default."""
        os.environ.pop("FLASK_ENV", None)
        config_class = get_config()
        assert config_class == DevelopmentConfig

    def test_get_config_production(self):
        """Test get_config returns production config when FLASK_ENV=production."""
        os.environ["FLASK_ENV"] = "production"
        config_class = get_config()
        assert config_class == ProductionConfig
        os.environ.pop("FLASK_ENV", None)

    def test_chart_colors(self):
        """Test chart color configuration."""
        config = Config()
        assert len(config.CHART_COLORS) == 3
        assert config.PRIMARY_COLOR == "#4682B4"
