"""
Flask backend for Tutoring Dashboard
"""
from flask import Flask, render_template, jsonify, request
from src.data_handler import SheetsDataHandler
from src.config import Config
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
data_handler = SheetsDataHandler()

# Helpers for date filtering (define before routes)
def _get_filter_params():
    return {
        'quick_range': request.args.get('quick_range', 'all'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
    }

def _apply_date_filter(df, params):
    if 'Datum:' not in df.columns:
        return df

    # Normalize date column once for all filters
    df = df.copy()
    df['Datum:'] = pd.to_datetime(df['Datum:'], errors='coerce')
    df = df.dropna(subset=['Datum:'])

    quick = params.get('quick_range', 'all') or 'all'
    start_raw = params.get('start_date')
    end_raw = params.get('end_date')

    start_dt = pd.to_datetime(start_raw, errors='coerce') if start_raw else None
    end_dt = pd.to_datetime(end_raw, errors='coerce') if end_raw else None

    # Relative shortcuts - calculate from TODAY, not max date
    if quick in {'last7', 'last30', 'last90'}:
        today = pd.Timestamp.now().normalize()
        days = {'last7': 7, 'last30': 30, 'last90': 90}[quick]
        cutoff = today - pd.Timedelta(days=days)
        return df[df['Datum:'] >= cutoff]

    # Custom or explicit range (inclusive end)
    if start_dt is not None or end_dt is not None:
        if start_dt is not None:
            df = df[df['Datum:'] >= start_dt]
        if end_dt is not None:
            inclusive_end = end_dt + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            df = df[df['Datum:'] <= inclusive_end]
        return df

    return df

@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    """Get key metrics for dashboard"""
    try:
        base_df = data_handler.fetch_data()
        params = _get_filter_params()
        filtered_df = _apply_date_filter(base_df, params)

        metrics = data_handler.get_key_metrics(filtered_df, base_df=base_df)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/top-students')
def get_top_students():
    """Get top students by revenue"""
    try:
        df = data_handler.fetch_data()
        
        # Group by student and aggregate metrics
        top_students = df.groupby('Name:').agg({
            'Lohn:': 'sum',
            'Stunden:': 'sum',
            'Datum:': 'count'  # Count sessions
        }).reset_index()
        
        # Rename columns
        top_students.columns = ['Name', 'Lohn', 'Stunden', 'Sessions']
        
        # Sort by revenue and get top 10
        top_students = top_students.sort_values('Lohn', ascending=False).head(10)
        
        return jsonify(top_students.to_dict('records'))
    except Exception as e:
        logger.error(f"Error fetching top students: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/monthly-summary')
def get_monthly_summary():
    params = _get_filter_params()
    df = data_handler.fetch_data()
    df = _apply_date_filter(df, params)
    # Parse Datum: to datetime if possible
    if 'Datum:' in df.columns:
        df['Datum:'] = pd.to_datetime(df['Datum:'], errors='coerce')
        df = df.dropna(subset=['Datum:'])
        df['YearMonth'] = df['Datum:'].dt.to_period('M').astype(str)
    else:
        # Fallback: no date column; return empty
        return jsonify({"months": [], "revenue": [], "hours": []})

    now_ts = pd.Timestamp.now()
    completed = df[df['Datum:'] <= now_ts]
    planned = df[df['Datum:'] > now_ts]

    def agg(sub):
        if sub.empty:
            return pd.DataFrame(columns=['YearMonth', 'Lohn:', 'Stunden:'])
        return sub.groupby('YearMonth').agg({
            'Lohn:': 'sum',
            'Stunden:': 'sum'
        }).reset_index()

    completed_g = agg(completed)
    planned_g = agg(planned)

    # Union of months to align arrays
    months = sorted(set(completed_g['YearMonth'].tolist()) | set(planned_g['YearMonth'].tolist()))

    def aligned(df_in, col):
        mapping = dict(zip(df_in['YearMonth'], df_in[col]))
        return [float(mapping.get(m, 0)) for m in months]

    return jsonify({
        "months": months,
        "revenue": aligned(completed_g, 'Lohn:'),
        "hours": aligned(completed_g, 'Stunden:'),
        "planned_revenue": aligned(planned_g, 'Lohn:'),
        "planned_hours": aligned(planned_g, 'Stunden:'),
    })

@app.route('/api/student-search')
def student_search():
    q = request.args.get('q', '').strip().lower()
    df = data_handler.fetch_data()
    if 'Name:' not in df.columns:
        return jsonify({"results": []})

    names = df['Name:'].astype(str).unique().tolist()
    if q:
        results = [n for n in names if q in n.lower()]
    else:
        results = names

    # Limit to top 20 for autocomplete
    return jsonify({"results": results[:20]})


@app.route('/api/student-details/<student_name>')
def get_student_details(student_name):
    """Get detailed information for a specific student"""
    try:
        df = data_handler.fetch_data()
        student_df = df[df['Name:'] == student_name]
        
        if student_df.empty:
            return jsonify({"error": "Student not found"}), 404
        
        details = {
            "name": student_name,
            "total_revenue": float(student_df['Lohn:'].sum()),
            "total_hours": float(student_df['Stunden:'].sum()),
            "total_sessions": len(student_df),
            "avg_hourly_rate": float(student_df['Lohn:'].sum() / student_df['Stunden:'].sum()),
            "sessions": [{"Datum": row['Datum:'], "Stunden": row['Stunden:'], "Lohn": row['Lohn:']} for _, row in student_df.iterrows()]
        }
        return jsonify(details)
    except Exception as e:
        logger.error(f"Error fetching student details: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/refresh')
def refresh_data():
    """Force refresh data from Google Sheets"""
    try:
        data_handler.fetch_data(force_refresh=True)
        return jsonify({"status": "success", "message": "Data refreshed"})
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
