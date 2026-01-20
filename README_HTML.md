# Tutoring Dashboard - HTML/CSS/JS Version

Modern tutoring business dashboard built with Flask, vanilla JavaScript, and beautiful CSS.

## 🚀 Quick Start

```bash
# Run the Flask app
python app_flask.py
```

Visit `http://localhost:8050` in your browser.

## 📁 Project Structure

```
Tutoring-Dashboard/
├── app_flask.py           # Flask backend with REST API
├── templates/             # HTML templates
│   └── index.html        # Main dashboard page
├── static/               # Frontend assets
│   ├── css/
│   │   └── style.css     # Modern CSS with animations
│   └── js/
│       └── app.js        # Dashboard JavaScript logic
├── src/                  # Python backend logic
│   ├── data_handler.py   # Google Sheets integration
│   ├── config.py         # Configuration
│   └── callbacks.py      # (Dash version - not used here)
├── dash_version/         # Old Dash files (archived)
└── requirements.txt      # Python dependencies
```

## 🎨 Features

- **Real-time Metrics**: 8 key KPIs with smooth animations
- **Top Students Table**: Click any row to see detailed session history
- **Date Filtering**: Quick ranges or custom date selection
- **Auto-refresh**: Data updates every 60 seconds
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Gradient highlights, hover effects, smooth transitions

## 🔧 API Endpoints

- `GET /` - Main dashboard page
- `GET /api/metrics?quick_range=all` - Key metrics with optional filtering
- `GET /api/top-students` - Top 10 students by revenue
- `GET /api/student-details/<name>` - Detailed student information
- `GET /api/refresh` - Force refresh data from Google Sheets

## 🌿 Branches

- `main` - Dash version (original)
- `html-rewrite` - Flask + HTML/CSS/JS version (this branch)

## 📝 Notes

The HTML version gives you complete control over the UI/UX while keeping all the Python data handling logic. You can now easily customize tables, add charts, or implement any UI pattern without Dash's limitations.
