"""Tests for callbacks module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.callbacks import DashboardCallbacks
from src.data_handler import SheetsDataHandler
from src.config import Config


class TestDashboardCallbacks:
    """Test cases for DashboardCallbacks."""

    @pytest.fixture
    def mock_app(self):
        """Create mock Dash app."""
        app = MagicMock()
        app.callback = MagicMock(return_value=lambda x: x)
        return app

    @pytest.fixture
    def mock_data_handler(self, mock_google_sheets_data):
        """Create mock data handler."""
        handler = MagicMock(spec=SheetsDataHandler)
        
        # Process sample data
        today = datetime.now()
        df = pd.DataFrame({
            "Datum:": [
                (today - timedelta(days=1)).date(),
                (today - timedelta(days=2)).date(),
                (today - timedelta(days=7)).date(),
            ],
            "Name:": ["Alice", "Bob", "Alice"],
            "Anfang": [
                pd.Timestamp(today.date().isoformat() + " 10:00"),
                pd.Timestamp(today.date().isoformat() + " 14:00"),
                pd.Timestamp(today.date().isoformat() + " 11:00"),
            ],
            "Ende": [
                pd.Timestamp(today.date().isoformat() + " 11:30"),
                pd.Timestamp(today.date().isoformat() + " 15:30"),
                pd.Timestamp(today.date().isoformat() + " 12:30"),
            ],
            "Stunden:": [1.5, 1.5, 1.5],
            "Lohn:": [30.0, 30.0, 30.0],
        })
        
        handler.fetch_data.return_value = df
        handler.get_monthly_summary.return_value = pd.DataFrame({
            "YearMonth": [pd.Period(today, "M")],
            "TotalIncome": [90.0],
            "TotalLessons": [4.5],
            "AverageHourlyWage": [20.0],
        })
        handler.get_yearly_summary.return_value = pd.DataFrame({
            "Year": [today.year],
            "TotalIncome": [90.0],
            "NumStudents": [2],
            "TotalLessons": [4.5],
            "AvgMonthlyIncome": [7.5],
            "AvgMonthlyHours": [0.375],
            "AvgMonthlyWage": [20.0],
            "YoYAvgMonthlyIncome": ["0.00%"],
            "YoYAvgMonthlyHours": ["0.00%"],
        })
        handler.get_student_summary.return_value = df[df["Name:"] == "Alice"]
        handler.get_top_students.return_value = pd.DataFrame({
            "Name:": ["Alice", "Bob"],
            "Lohn:": [60.0, 30.0],
        })
        handler.get_total_stats.return_value = {
            "total_hours": 4.5,
            "total_income": 90.0,
        }
        
        return handler

    def test_init(self, mock_app, mock_data_handler):
        """Test DashboardCallbacks initialization."""
        callbacks = DashboardCallbacks(mock_app, mock_data_handler)
        
        assert callbacks.app == mock_app
        assert callbacks.data_handler == mock_data_handler
        assert callbacks.config is not None

    def test_create_yearly_cards(self, mock_app, mock_data_handler):
        """Test yearly card creation."""
        today = datetime.now()
        yearly_data = pd.DataFrame({
            "Year": [today.year],
            "TotalIncome": [90.0],
            "NumStudents": [2],
            "AvgMonthlyIncome": [7.5],
            "AvgMonthlyWage": [20.0],
            "AvgMonthlyHours": [0.375],
            "YoYAvgMonthlyIncome": ["0.00%"],
            "YoYAvgMonthlyHours": ["0.00%"],
        })
        
        callbacks = DashboardCallbacks(mock_app, mock_data_handler)
        cards = callbacks._create_yearly_cards(yearly_data)
        
        assert len(cards) == 1
        assert cards[0].children is not None

    def test_create_monthly_chart(self, mock_app, mock_data_handler):
        """Test monthly chart creation."""
        today = datetime.now()
        monthly_data = pd.DataFrame({
            "YearMonth": [pd.Period(today, "M")],
            "TotalIncome": [90.0],
        })
        
        callbacks = DashboardCallbacks(mock_app, mock_data_handler)
        fig = callbacks._create_monthly_chart(monthly_data)
        
        assert fig is not None
        assert hasattr(fig, "data")
        assert len(fig.data) > 0

    def test_create_monthly_chart_empty_data(self, mock_app, mock_data_handler):
        """Test monthly chart with empty data."""
        callbacks = DashboardCallbacks(mock_app, mock_data_handler)
        fig = callbacks._create_monthly_chart(pd.DataFrame())
        
        assert fig is not None

    def test_callbacks_registered(self, mock_app, mock_data_handler):
        """Test that callbacks are registered."""
        DashboardCallbacks(mock_app, mock_data_handler)
        
        # Check that app.callback was called
        assert mock_app.callback.called
