# Development Guide (Short)

## Architecture
- Dash app with callbacks separated from layout.
- Data layer: `SheetsDataHandler` fetches and caches Google Sheets data.
- Config: `Config` + env (`.env`) for IDs/ports.
- UI: `src/app.py` layout + `assets/custom.css` styling.

## Key files
- `run.py` (entry from WebApps)
- `src/app.py` (layout, wiring)
- `src/callbacks.py` (all interactions, charts)
- `src/data_handler.py` (fetch, clean, aggregate, date filtering)
- `src/config.py` (settings)
- `tests/` (pytest suite)

## Commands
From `WebApps` (venv active):
- Run app: `python run.py`
- Tests: `cd Tutoring-Dashboard && ../.venv/bin/python -m pytest`
- Lint/format (optional): `pip install black flake8 isort mypy` then run your preferred tools.

## Data & filters
- Service account: `keys.json` in `Tutoring-Dashboard/`
- Range: `Daten!A1:H`, spreadsheet id via `SAMPLE_SPREADSHEET_ID` in `.env`
- Date filters: quick presets (30/90/YTD/All) or custom range; applied to charts, table, summaries.

## Testing notes
- Uses pytest; fixtures live in `tests/fixtures`.
- If NumPy/pandas version issues occur, upgrade pandas/pyarrow or pin numpy<2 if needed.

## Deployment tips
- Set `FLASK_ENV=production`, `DEBUG=false`, adjust `HOST`/`PORT`.
- Provide correct `.env` and `keys.json` on the server.
