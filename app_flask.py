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

@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    """Get key metrics for dashboard"""
    try:
        df = data_handler.fetch_data()
        
        # Apply date filtering if provided
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        quick_range = request.args.get('quick_range', 'all')
        
        if quick_range != 'all':
            if quick_range == 'last7':
                df = df[df['Datum:'] >= (df['Datum:'].max() - pd.Timedelta(days=7))]
            elif quick_range == 'last30':
                df = df[df['Datum:'] >= (df['Datum:'].max() - pd.Timedelta(days=30))]
            elif quick_range == 'last90':
                df = df[df['Datum:'] >= (df['Datum:'].max() - pd.Timedelta(days=90))]
        elif start_date and end_date:
            df = df[(df['Datum:'] >= start_date) & (df['Datum:'] <= end_date)]
        
        metrics = data_handler.get_key_metrics(df)
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

    grouped = df.groupby('YearMonth').agg({
        'Lohn:': 'sum',
        'Stunden:': 'sum'
    }).reset_index().sort_values('YearMonth')

    return jsonify({
        "months": grouped['YearMonth'].tolist(),
        "revenue": [float(x) for x in grouped['Lohn:'].tolist()],
        "hours": [float(x) for x in grouped['Stunden:'].tolist()],
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

# Helpers for date filtering
def _get_filter_params():
    return {
        'quick_range': request.args.get('quick_range', 'all'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
    }

def _apply_date_filter(df, params):
    # Ensure Datum: is datetime for comparisons
    if 'Datum:' in df.columns:
        df['Datum:'] = pd.to_datetime(df['Datum:'], errors='coerce')
        df = df.dropna(subset=['Datum:'])

    quick = params.get('quick_range', 'all')
    start = params.get('start_date')
    end = params.get('end_date')

    if quick and quick != 'all' and 'Datum:' in df.columns:
        max_date = df['Datum:'].max()
        if pd.isna(max_date):
            return df
        if quick == 'last7':
            cutoff = max_date - pd.Timedelta(days=7)
            return df[df['Datum:'] >= cutoff]
        if quick == 'last30':
            cutoff = max_date - pd.Timedelta(days=30)
            return df[df['Datum:'] >= cutoff]
        if quick == 'last90':
            cutoff = max_date - pd.Timedelta(days=90)
            return df[df['Datum:'] >= cutoff]
        return df
    elif start and end and 'Datum:' in df.columns:
        start_dt = pd.to_datetime(start, errors='coerce')
        end_dt = pd.to_datetime(end, errors='coerce')
        if pd.isna(start_dt) or pd.isna(end_dt):
            return df
        return df[(df['Datum:'] >= start_dt) & (df['Datum:'] <= end_dt)]
    else:
        return df
