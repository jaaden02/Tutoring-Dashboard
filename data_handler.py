import pandas as pd
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Google Sheets setup
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

SAMPLE_SPREADSHEET_ID = os.getenv("SAMPLE_SPREADSHEET_ID")
SAMPLE_RANGE_NAME = "Daten!A1:H"

last_fetch_time = 0

def fetch_data_from_sheets():
    """Fetch data from Google Sheets and return as a DataFrame."""
    global last_fetch_time, data_cache
    current_time = time.time()
    # Only fetch data if more than 10 seconds have passed since the last fetch or if cache is empty
    if current_time - last_fetch_time > 10 or data_cache is None:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
        values = result.get("values", [])

        # Create DataFrame and specify headers directly
        df = pd.DataFrame(values[1:], columns=values[0])

        # Convert Datum: to datetime
        df['Datum:'] = pd.to_datetime(df['Datum:'], errors='coerce', format='%d.%m.%Y')

        # Remove rows where Datum: could not be converted
        df = df[df['Datum:'].notna()]

        # Convert Anfang: and Ende: to datetime based on Datum:
        df['Anfang:'] = pd.to_datetime(df['Anfang:'], errors='coerce', format='%H:%M')
        df['Ende:'] = pd.to_datetime(df['Ende:'], errors='coerce', format='%H:%M')

        # Combine Datum: with Anfang: and Ende: to create full datetime
        df['Anfang'] = pd.to_datetime(df['Datum:'].astype(str) + ' ' + df['Anfang:'].dt.strftime('%H:%M'), errors='coerce')
        df['Ende'] = pd.to_datetime(df['Datum:'].astype(str) + ' ' + df['Ende:'].dt.strftime('%H:%M'), errors='coerce')

        # Drop unnecessary columns in a single step
        df = df.drop(columns=['Anbieter:', 'Anfang:', 'Ende:'])

        # Remove rows where 'Names' column is missing
        df = df[df['Name:'].notna()]

        # Convert Stunden: and Lohn: to numeric, handling commas and non-numeric gracefully
        df['Stunden:'] = pd.to_numeric(df['Stunden:'].str.replace(',', '.'), errors='coerce')
        df['Lohn:'] = pd.to_numeric(df['Lohn:'].str.replace(',', '.'), errors='coerce')

        # Cache the cleaned data
        data_cache = df
        last_fetch_time = current_time

    return data_cache

def create_summary_dataframe(df):
    """Create a second DataFrame with income per month, total number of lessons, and average hourly wage."""
    df['EndDateTime'] = df.apply(lambda row: pd.Timestamp.combine(row['Datum:'].date(), row['Ende'].time()) if pd.notna(row['Datum:']) and pd.notna(row['Ende']) else pd.NaT, axis=1)
    df = df[df['EndDateTime'] < pd.Timestamp.now()]
    
    df['YearMonth'] = df['Datum:'].dt.to_period('M')
    
    summary_df = df.groupby('YearMonth').agg(
        TotalIncome=('Lohn:', 'sum'),
        TotalLessons=('Stunden:', 'sum'),
        AverageHourlyWage=('Lohn:', lambda x: (x.sum() / df.loc[x.index, 'Stunden:'].sum()) if df.loc[x.index, 'Stunden:'].sum() > 0 else 0)
    ).reset_index()
    return summary_df

def create_yearly_income_summary(df):
    """Create a DataFrame summarizing the yearly income."""
    df['Year'] = df['Datum:'].dt.year
    yearly_summary = df.groupby('Year').agg(
        TotalIncome=('Lohn:', 'sum'),
        NumStudents=('Name:', 'nunique'),
        TotalLessons=('Stunden:', 'sum')
    ).reset_index()
    
    yearly_summary['AvgMonthlyIncome'] = yearly_summary['TotalIncome'] / 12
    yearly_summary['AvgMonthlyHours'] = yearly_summary['TotalLessons'] / 12
    yearly_summary['AvgMonthlyWage'] = yearly_summary.apply(
        lambda row: row['TotalIncome'] / row['TotalLessons'] if row['TotalLessons'] > 0 else 0, axis=1
    )
    
    yearly_summary['YoYAvgMonthlyIncome'] = yearly_summary['AvgMonthlyIncome'].pct_change().fillna(0).apply(lambda x: f"{x:.2%}")
    yearly_summary['YoYAvgMonthlyHours'] = yearly_summary['AvgMonthlyHours'].pct_change().fillna(0).apply(lambda x: f"{x:.2%}")
    
    return yearly_summary
