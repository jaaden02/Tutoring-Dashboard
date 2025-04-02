Sure! Here’s a shorter version of the README:

⸻

📊 Tutoring Dashboard

A Dash web app that reads tutoring data from Google Sheets and displays income summaries, trends, and student-specific stats.

⸻

⚙️ Features
	•	🔄 Live Google Sheets integration
	•	📅 Monthly & yearly income summaries
	•	🎯 Student-specific stats & search
	•	📈 Interactive Plotly charts
	•	🔘 Manual data refresh

⸻

🚀 Setup
	1.	Install dependencies:

pip install -r requirements.txt


	2.	Add a .env file with your Google Sheet ID:

SAMPLE_SPREADSHEET_ID=your_sheet_id


	3.	Place keys.json (Google service account) in the project root.
	4.	Run the app:

python app.py



⸻

📝 Notes
	•	Requires columns like Datum:, Stunden:, Lohn:, Name:
	•	Uses Dash, Plotly, Bootstrap, and Google Sheets API

⸻

Let me know if you want a requirements.txt auto-generated.
