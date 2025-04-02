import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from data_handler import fetch_data_from_sheets
from callbacks import setup_callbacks

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.5.0/font/bootstrap-icons.min.css'])

app.layout = dbc.Container([
    # Header row
    dbc.Row([
        dbc.Col(html.H1("My Tutoring Dashboard", className="text-center mb-4"), width=12)
    ]),
    # Yearly income summary row
    dbc.Row(id='yearly-income-summary-row', className='mb-4'),
    # Total summary row (added for total hours and income)
    dbc.Row(id='total-summary-row', className='mb-4'),
    # Refresh button row
    dbc.Row([
        dbc.Col(dbc.Button("Refresh Data", id="refresh-button", n_clicks=0, color="primary", className="mb-4"), width=12)
    ]),
    # Student search row
    dbc.Row([
        dbc.Col(
            dbc.Input(id='student-search', type='text', placeholder='Enter student name...', className='mb-4'),
            width=12
        ),
    ]),
    dbc.Row(id='student-summary-row', className='mb-4'),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='top-10-students-graph'),
            width=12
        )
    ]),
    # Data table row
    dbc.Row([
        dbc.Col(
            dash_table.DataTable(
                id='data-table',
                columns=[{"name": i, "id": i} for i in fetch_data_from_sheets().columns if i not in ['Anbieter', 'Datum:', 'Anfang:', 'Ende:']],
                data=fetch_data_from_sheets().to_dict('records'),
                page_size=10,
                filter_action="native",
                sort_action="native",
                style_table={'overflowX': 'auto'}
            ), width=12
        )
    ]),
    # Monthly income bar chart
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='monthly-income-graph'),
            width=12
        )
    ])
], fluid=True)



# Setup callbacks
setup_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
