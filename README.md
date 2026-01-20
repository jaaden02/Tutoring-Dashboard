# Tutoring Dashboard

A slim guide to run and use the dashboard.

## Overview
- Dash app reading Google Sheets (revenue, lessons, top students).
- Smart cache (10s), date filters (Last 30/90, YTD, All, Custom), search by student.
- Charts: monthly income, top earners; data table with filtering/sorting.

## Quick start
1) From `WebApps`, activate venv: `source .venv/bin/activate`
2) Install deps: `pip install -r Tutoring-Dashboard/requirements.txt`
3) Credentials/config:
   - `keys.json` in `Tutoring-Dashboard/`
   - Copy `.env.example` to `.env`; set `SAMPLE_SPREADSHEET_ID`, `PORT`, `HOST`, `DEBUG`
4) Run (from WebApps): `python run.py`
5) Open: http://127.0.0.1:8050/

## Usage
- Refresh data with the top button.
- Time filters: pick preset or custom range; all charts/table update.
- Search: type part of a student name to see their summary.
- Table: filter/sort inline; page size 10.

## Structure
- Entry: `run.py`
- App shell: `src/app.py`; callbacks: `src/callbacks.py`; data: `src/data_handler.py`; config: `src/config.py`
- Styling: `assets/custom.css`
- Tests: `tests/`

## Testing
From `Tutoring-Dashboard/` (venv active):
```
../.venv/bin/python -m pytest
```

## Troubleshooting
- Sheets errors: verify `keys.json` path and `SAMPLE_SPREADSHEET_ID`.
- Empty charts/table: check date range filter.
- Reload path errors: reloader disabled in app run settings.
