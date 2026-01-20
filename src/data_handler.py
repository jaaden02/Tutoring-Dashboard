"""Data handling module for Google Sheets integration."""
import logging
import time
from typing import Optional, Dict
from datetime import datetime

import pandas as pd

from .config import Config

logger = logging.getLogger(__name__)


class SheetsDataHandler:
    """Handles fetching and processing data from Google Sheets."""

    def __init__(self, config: Config = None):
        """Initialize the data handler.
        
        Args:
            config: Configuration object. Uses default Config if None.
        """
        self.config = config or Config()
        self._cache: Optional[pd.DataFrame] = None
        self._last_fetch_time: float = 0
        self._credentials = None

    def _get_credentials(self):
        """Get and return service account credentials."""
        try:
            # Lazy import to avoid heavy modules at startup
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_file(
                self.config.SERVICE_ACCOUNT_FILE,
                scopes=self.config.SCOPES
            )
        except FileNotFoundError:
            logger.error(f"Service account file not found: {self.config.SERVICE_ACCOUNT_FILE}")
            raise

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed based on TTL."""
        current_time = time.time()
        return (
            self._cache is None or
            (current_time - self._last_fetch_time) > self.config.CACHE_TTL
        )

    def fetch_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch data from Google Sheets with caching.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data.
            
        Returns:
            DataFrame with cleaned lesson data.
        """
        if not force_refresh and not self._should_refresh_cache():
            return self._cache

        try:
            if self._credentials is None:
                self._credentials = self._get_credentials()
            # Lazy import to avoid heavy modules at startup
            from googleapiclient.discovery import build
            service = build("sheets", "v4", credentials=self._credentials)
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=self.config.SHEET_RANGE
            ).execute()

            values = result.get("values", [])
            if not values or len(values) < 2:
                logger.warning("No data returned from Google Sheets")
                return pd.DataFrame()

            df = self._process_data(values)
            self._cache = df
            self._last_fetch_time = time.time()
            logger.info(f"Fetched {len(df)} records from Google Sheets")
            return df

        except Exception as e:
            logger.error(f"Error fetching data from Google Sheets: {e}")
            raise

    def _process_data(self, values: list) -> pd.DataFrame:
        """Process raw sheet values into clean DataFrame.
        
        Args:
            values: Raw values from Google Sheets API.
            
        Returns:
            Cleaned DataFrame.
        """
        # Create DataFrame with headers from first row
        df = pd.DataFrame(values[1:], columns=values[0])

        # Parse dates
        df["Datum:"] = pd.to_datetime(
            df["Datum:"], errors="coerce", format=self.config.DATE_FORMAT
        )
        df = df[df["Datum:"].notna()]

        # Parse times
        df["Anfang:"] = pd.to_datetime(
            df["Anfang:"], errors="coerce", format=self.config.TIME_FORMAT
        )
        df["Ende:"] = pd.to_datetime(
            df["Ende:"], errors="coerce", format=self.config.TIME_FORMAT
        )

        # Combine date and time columns
        df["Anfang"] = pd.to_datetime(
            df["Datum:"].astype(str) + " " + df["Anfang:"].dt.strftime(self.config.TIME_FORMAT),
            errors="coerce",
        )
        df["Ende"] = pd.to_datetime(
            df["Datum:"].astype(str) + " " + df["Ende:"].dt.strftime(self.config.TIME_FORMAT),
            errors="coerce",
        )

        # Drop unnecessary columns
        df = df.drop(columns=["Anbieter:", "Anfang:", "Ende:"])

        # Remove rows with missing or empty names
        df = df[df["Name:"].notna()]
        df = df[df["Name:"].str.strip() != ""]

        # Convert numeric columns, handling German decimal format
        df["Stunden:"] = pd.to_numeric(
            df["Stunden:"].str.replace(",", "."), errors="coerce"
        )
        df["Lohn:"] = pd.to_numeric(
            df["Lohn:"].str.replace(",", "."), errors="coerce"
        )

        return df.reset_index(drop=True)

    def get_monthly_summary(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Create monthly summary DataFrame.
        
        Args:
            df: Input DataFrame. Uses cached data if None.
            
        Returns:
            DataFrame with monthly aggregations.
        """
        if df is None:
            df = self.fetch_data()

        if df.empty:
            return pd.DataFrame()

        # Filter to only completed lessons
        df = df.copy()
        df["EndDateTime"] = df.apply(
            lambda row: pd.Timestamp.combine(
                row["Datum:"].date(), row["Ende"].time()
            )
            if pd.notna(row["Datum:"]) and pd.notna(row["Ende"])
            else pd.NaT,
            axis=1,
        )
        df = df[df["EndDateTime"] < pd.Timestamp.now()]

        if df.empty:
            return pd.DataFrame()

        df["YearMonth"] = df["Datum:"].dt.to_period("M")

        summary = df.groupby("YearMonth", as_index=False).agg(
            TotalIncome=("Lohn:", "sum"),
            TotalLessons=("Stunden:", "sum"),
        )

        # Calculate average hourly wage
        summary["AverageHourlyWage"] = summary.apply(
            lambda row: (
                row["TotalIncome"] / row["TotalLessons"]
                if row["TotalLessons"] > 0
                else 0
            ),
            axis=1,
        )

        return summary

    def get_yearly_summary(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Create yearly summary DataFrame.
        
        Args:
            df: Input DataFrame. Uses cached data if None.
            
        Returns:
            DataFrame with yearly aggregations and metrics.
        """
        if df is None:
            df = self.fetch_data()

        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        df["Year"] = df["Datum:"].dt.year

        summary = df.groupby("Year", as_index=False).agg(
            TotalIncome=("Lohn:", "sum"),
            NumStudents=("Name:", "nunique"),
            TotalLessons=("Stunden:", "sum"),
        )

        # Calculate derived metrics
        summary["AvgMonthlyIncome"] = summary["TotalIncome"] / 12
        summary["AvgMonthlyHours"] = summary["TotalLessons"] / 12
        summary["AvgMonthlyWage"] = summary.apply(
            lambda row: (
                row["TotalIncome"] / row["TotalLessons"]
                if row["TotalLessons"] > 0
                else 0
            ),
            axis=1,
        )

        # Calculate year-over-year changes
        summary["YoYAvgMonthlyIncome"] = (
            summary["AvgMonthlyIncome"]
            .pct_change()
            .fillna(0)
            .apply(lambda x: f"{x:.2%}")
        )
        summary["YoYAvgMonthlyHours"] = (
            summary["AvgMonthlyHours"]
            .pct_change()
            .fillna(0)
            .apply(lambda x: f"{x:.2%}")
        )

        return summary

    def get_student_summary(
        self, student_name: str, df: Optional[pd.DataFrame] = None
    ) -> Optional[pd.DataFrame]:
        """Get summary for a specific student.
        
        Args:
            student_name: Name of the student to search for.
            df: Input DataFrame. Uses cached data if None.
            
        Returns:
            DataFrame with student data or None if not found.
        """
        if df is None:
            df = self.fetch_data()

        if df.empty or not student_name:
            return None

        student_df = df[df["Name:"].str.contains(student_name, case=False, na=False)]
        return student_df if not student_df.empty else None

    def get_top_students(
        self, n: int = None, df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Get top N students by income.
        
        Args:
            n: Number of students to return. Uses config default if None.
            df: Input DataFrame. Uses cached data if None.
            
        Returns:
            DataFrame with top students sorted by income.
        """
        if n is None:
            n = self.config.TOP_STUDENTS_COUNT

        if df is None:
            df = self.fetch_data()

        if df.empty:
            return pd.DataFrame()

        return (
            df.groupby("Name:")["Lohn:"]
            .sum()
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
        )

    def get_total_stats(self, df: Optional[pd.DataFrame] = None) -> dict:
        """Get total statistics across all data.
        
        Args:
            df: Input DataFrame. Uses cached data if None.
            
        Returns:
            Dictionary with total hours and income.
        """
        if df is None:
            df = self.fetch_data()

        return {
            "total_hours": df["Stunden:"].sum() if not df.empty else 0,
            "total_income": df["Lohn:"].sum() if not df.empty else 0,
        }

    def get_key_metrics(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Calculate comprehensive key metrics for dashboard overview.
        
        Args:
            df: Input DataFrame. Uses cached data if None.
            
        Returns:
            Dictionary with key performance metrics.
        """
        if df is None:
            df = self.fetch_data()

        if df.empty:
            return {
                "total_revenue": 0,
                "total_hours": 0,
                "avg_hourly_rate": 0,
                "unique_students": 0,
                "total_sessions": 0,
                "avg_session_length": 0,
                "this_month_revenue": 0,
                "this_month_hours": 0,
            }

        # Use the most recent month present in the (filtered) data instead of calendar month
        latest_date = df["Datum:"].max()
        latest_month_mask = df["Datum:"].dt.to_period("M") == latest_date.to_period("M")
        latest_month = df[latest_month_mask]

        total_revenue = df["Lohn:"].sum()
        total_hours = df["Stunden:"].sum()
        
        return {
            "total_revenue": total_revenue,
            "total_hours": total_hours,
            "avg_hourly_rate": total_revenue / total_hours if total_hours > 0 else 0,
            "unique_students": df["Name:"].nunique(),
            "total_sessions": len(df),
            "avg_session_length": df["Stunden:"].mean() if not df.empty else 0,
            "this_month_revenue": latest_month["Lohn:"].sum() if not latest_month.empty else 0,
            "this_month_hours": latest_month["Stunden:"].sum() if not latest_month.empty else 0,
        }

    def filter_by_date(
        self,
        df: Optional[pd.DataFrame],
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        """Filter DataFrame by inclusive date range on Datum: column.
        
        Args:
            df: DataFrame to filter. Uses cached data if None.
            start_date: Inclusive start date as Timestamp or None.
            end_date: Inclusive end date as Timestamp or None.
        
        Returns:
            Filtered DataFrame.
        """
        if df is None:
            df = self.fetch_data()

        if df.empty:
            return df

        filtered = df.copy()
        if start_date is not None:
            filtered = filtered[filtered["Datum:"] >= start_date.normalize()]
        if end_date is not None:
            # Add one day to make the end date inclusive to the end of day
            inclusive_end = end_date.normalize() + pd.Timedelta(days=1)
            filtered = filtered[filtered["Datum:"] < inclusive_end]
        return filtered.reset_index(drop=True)

    def clear_cache(self):
        """Clear the data cache."""
        self._cache = None
        self._last_fetch_time = 0
        logger.info("Data cache cleared")
