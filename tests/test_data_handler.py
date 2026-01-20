"""Tests for data_handler module."""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_handler import SheetsDataHandler
from src.config import Config


class TestSheetsDataHandler:
    """Test cases for SheetsDataHandler class."""

    @pytest.fixture
    def handler(self, config):
        """Create handler with mocked credentials."""
        with patch("src.data_handler.service_account.Credentials"):
            handler = SheetsDataHandler(config)
            handler._credentials = Mock()
            return handler

    def test_init(self, config):
        """Test handler initialization."""
        with patch("src.data_handler.service_account.Credentials"):
            handler = SheetsDataHandler(config)
            assert handler.config == config
            assert handler._cache is None
            assert handler._last_fetch_time == 0

    def test_should_refresh_cache_with_none_cache(self, handler):
        """Test cache refresh check when cache is None."""
        assert handler._should_refresh_cache() is True

    def test_should_refresh_cache_expired(self, handler):
        """Test cache refresh check with expired TTL."""
        handler._cache = pd.DataFrame()
        handler._last_fetch_time = 0
        assert handler._should_refresh_cache() is True

    def test_should_refresh_cache_valid(self, handler, config):
        """Test cache refresh check with valid cache."""
        import time
        handler._cache = pd.DataFrame()
        handler._last_fetch_time = time.time()
        handler.config.CACHE_TTL = 100
        assert handler._should_refresh_cache() is False

    def test_process_data_basic(self, handler, mock_google_sheets_data):
        """Test basic data processing."""
        df = handler._process_data(mock_google_sheets_data)
        
        assert len(df) == 3
        assert "Datum:" in df.columns
        assert "Name:" in df.columns
        assert "Stunden:" in df.columns
        assert "Lohn:" in df.columns
        assert "Anfang" in df.columns
        assert "Ende" in df.columns

    def test_process_data_numeric_conversion(self, handler, mock_google_sheets_data):
        """Test numeric column conversion."""
        df = handler._process_data(mock_google_sheets_data)
        
        assert df["Stunden:"].dtype in [float, "float64"]
        assert df["Lohn:"].dtype in [float, "float64"]
        assert df["Stunden:"].iloc[0] == 1.5
        assert df["Lohn:"].iloc[0] == 30.0

    def test_process_data_date_conversion(self, handler, mock_google_sheets_data):
        """Test date conversion."""
        df = handler._process_data(mock_google_sheets_data)
        
        assert pd.api.types.is_datetime64_any_dtype(df["Datum:"])
        assert df["Datum:"].notna().all()

    def test_process_data_removes_missing_names(self, handler):
        """Test that rows with missing names are removed."""
        today = datetime.now()
        data = [
            ["Datum:", "Name:", "Anfang:", "Ende:", "Anbieter:", "Stunden:", "Lohn:"],
            [today.strftime("%d.%m.%Y"), "Alice", "10:00", "11:00", "School", "1", "30,00"],
            [today.strftime("%d.%m.%Y"), "", "14:00", "15:00", "School", "1", "30,00"],
        ]
        df = handler._process_data(data)
        
        assert len(df) == 1
        assert df["Name:"].iloc[0] == "Alice"

    def test_fetch_data_with_mock(self, handler, mock_google_sheets_data):
        """Test data fetching with mock API."""
        with patch("src.data_handler.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": mock_google_sheets_data
            }

            df = handler.fetch_data(force_refresh=True)
            
            assert len(df) == 3
            assert not df.empty

    def test_fetch_data_caching(self, handler, mock_google_sheets_data):
        """Test that data is cached."""
        with patch("src.data_handler.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": mock_google_sheets_data
            }

            # First fetch
            df1 = handler.fetch_data(force_refresh=True)
            # Second fetch should use cache
            df2 = handler.fetch_data(force_refresh=False)
            
            assert df1.equals(df2)

    def test_get_monthly_summary(self, handler, mock_google_sheets_data):
        """Test monthly summary creation."""
        df = handler._process_data(mock_google_sheets_data)
        summary = handler.get_monthly_summary(df)
        
        assert not summary.empty
        assert "YearMonth" in summary.columns
        assert "TotalIncome" in summary.columns
        assert "TotalLessons" in summary.columns
        assert "AverageHourlyWage" in summary.columns

    def test_get_yearly_summary(self, handler, mock_google_sheets_data):
        """Test yearly summary creation."""
        df = handler._process_data(mock_google_sheets_data)
        summary = handler.get_yearly_summary(df)
        
        assert not summary.empty
        assert "Year" in summary.columns
        assert "TotalIncome" in summary.columns
        assert "NumStudents" in summary.columns
        assert "AvgMonthlyIncome" in summary.columns
        assert "AvgMonthlyWage" in summary.columns

    def test_get_student_summary(self, handler, mock_google_sheets_data):
        """Test student summary retrieval."""
        df = handler._process_data(mock_google_sheets_data)
        student_df = handler.get_student_summary("Alice", df)
        
        assert student_df is not None
        assert len(student_df) == 2
        assert all(student_df["Name:"] == "Alice")

    def test_get_student_summary_not_found(self, handler, mock_google_sheets_data):
        """Test student summary when student not found."""
        df = handler._process_data(mock_google_sheets_data)
        student_df = handler.get_student_summary("NonExistent", df)
        
        assert student_df is None

    def test_get_top_students(self, handler, mock_google_sheets_data):
        """Test top students retrieval."""
        df = handler._process_data(mock_google_sheets_data)
        top = handler.get_top_students(n=2, df=df)
        
        assert len(top) <= 2
        assert "Name:" in top.columns
        assert "Lohn:" in top.columns

    def test_get_total_stats(self, handler, mock_google_sheets_data):
        """Test total statistics calculation."""
        df = handler._process_data(mock_google_sheets_data)
        stats = handler.get_total_stats(df)
        
        assert "total_hours" in stats
        assert "total_income" in stats
        assert stats["total_hours"] > 0
        assert stats["total_income"] > 0

    def test_clear_cache(self, handler):
        """Test cache clearing."""
        handler._cache = pd.DataFrame({"test": [1, 2, 3]})
        handler._last_fetch_time = 123456
        
        handler.clear_cache()
        
        assert handler._cache is None
        assert handler._last_fetch_time == 0
