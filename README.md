# Tutoring Dashboard (Flask + HTML/JS)

Modern tutoring dashboard using Flask for APIs and vanilla HTML/CSS/JS for the UI.

## Quick Start
```bash
cd /Users/jasperaden/Documents/Programmieren/WebApps/Tutoring-Dashboard
source ../.venv/bin/activate
python -m pip install -r requirements.txt
python app_flask.py
```
Then open http://localhost:8050

## Configuration
- Copy `.env.example` to `.env` and set:
   - `SPREADSHEET_ID` (Google Sheet)
   - `SHEET_RANGE` (e.g., `Sheet1!A:Z`)
   - `SERVICE_ACCOUNT_FILE` (path to `keys.json`)
- Place `keys.json` in the project root or point `SERVICE_ACCOUNT_FILE` to its location.

## Features
- KPIs: total/avg metrics, latest-month metrics, upcoming sessions & prospective income
- Filters: quick ranges and custom date window
- Charts: monthly revenue/hours (actual vs planned), top students
- Search: student autocomplete + details modal
- Auto-refresh (60s) and manual refresh button

## API Endpoints
- `/` — HTML dashboard
- `/api/metrics` — KPIs (supports `quick_range`, `start_date`, `end_date`)
- `/api/monthly-summary` — Monthly actual vs planned revenue/hours
- `/api/top-students` — Top students by revenue
- `/api/student-details/<name>` — Detail view with recent sessions
- `/api/student-search` — Autocomplete names
- `/api/refresh` — Force data refresh

## Project Structure
- `app_flask.py` — Flask app and routes
- `src/data_handler.py` — Google Sheets fetch + metrics (actual/planned split)
- `static/` — CSS/JS assets
- `templates/index.html` — Dashboard UI
- `run_html.sh` — Helper script to start the app
- `tests/` — Pytest placeholder

## Data Expectations
- Uses column names with colons from the sheet (e.g., `Name:`, `Datum:`, `Stunden:`, `Lohn:`).
- Planned vs completed split is based on `Datum:` relative to now.

## Testing
```bash
cd /Users/jasperaden/Documents/Programmieren/WebApps/Tutoring-Dashboard
source ../.venv/bin/activate
python -m pytest
```

## Notes
- This repo now uses the Flask/HTML version as main. Legacy Dash assets have been removed.
