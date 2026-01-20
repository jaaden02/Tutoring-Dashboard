"""Tests for the main Dash application."""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.app import TutoringDashboardApp, create_app
from src.config import Config


class TestTutoringDashboardApp:
    """Test cases for TutoringDashboardApp."""

    def test_init(self):
        """Test app initialization."""
        with patch("src.app.SheetsDataHandler"):
            app = TutoringDashboardApp()
            
            assert app.config is not None
            assert app.data_handler is not None
            assert app.app is not None

    def test_create_app(self):
        """Test Dash app creation."""
        with patch("src.app.SheetsDataHandler"):
            app = TutoringDashboardApp()
            
            assert app.app is not None
            assert hasattr(app.app, "layout")

    def test_layout_contains_key_elements(self):
        """Test that layout contains key elements."""
        with patch("src.app.SheetsDataHandler"):
            app = TutoringDashboardApp()
            layout = app.app.layout
            
            # Check that layout is not None
            assert layout is not None

    def test_create_app_factory(self):
        """Test create_app factory function."""
        with patch("src.app.SheetsDataHandler"):
            dash_app = create_app()
            
            assert dash_app is not None
            assert hasattr(dash_app, "layout")

    def test_run_method_exists(self):
        """Test that run method exists."""
        with patch("src.app.SheetsDataHandler"):
            app = TutoringDashboardApp()
            
            assert hasattr(app, "run")
            assert callable(app.run)
