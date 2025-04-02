import dash
from dash.dependencies import Input, Output, State
from data_handler import fetch_data_from_sheets, create_summary_dataframe, create_yearly_income_summary
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import html

def setup_callbacks(app):
    @app.callback(
        [Output('data-table', 'data'), Output('monthly-income-graph', 'figure'), Output('yearly-income-summary-row', 'children')],
        Input('refresh-button', 'n_clicks')
    )
    def refresh_data(n_clicks):
        # Update data only if the refresh button has been clicked
        df = fetch_data_from_sheets()
        if n_clicks > 0:
            df = fetch_data_from_sheets()
        
        # Create the summary DataFrame
        summary_df = create_summary_dataframe(df)
        yearly_summary = create_yearly_income_summary(df)

        # Create yearly income summary boxes
        yearly_income_boxes = [
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"Year: {row['Year']}", className="card-title"),
                        html.H5(f"Total Income: {row['TotalIncome']} €", className="card-text")
                    ]),
                    dbc.Collapse(
                        dbc.CardBody([
                            html.H5(f"Number of Different Students: {row['NumStudents']}", className="card-text"),
                            html.H5(f"Average Monthly Income: {row['AvgMonthlyIncome']:.2f} €", className="card-text"),
                            html.H5(f"Average Monthly Wage: {row['AvgMonthlyWage']:.2f} €", className="card-text"),
                            html.H5(f"Average Monthly Number of Hours: {row['AvgMonthlyHours']:.2f}", className="card-text"),
                            html.H5(f"YoY Avg Monthly Income: {row['YoYAvgMonthlyIncome']}", className="card-text"),
                            html.H5(f"YoY Avg Monthly Hours: {row['YoYAvgMonthlyHours']}", className="card-text")
                        ]),
                        id={'type': 'collapse', 'index': row['Year']},
                        is_open=False
                    ),
                    dbc.Button(
                        html.I(className='bi bi-chevron-down'),
                        id={'type': 'toggle-button', 'index': row['Year']},
                        color="link", n_clicks=0,
                        style={'position': 'absolute', 'top': '5px', 'right': '10px', 'fontSize': '1.5em', 'color': 'white'}
                    )
                ], className="text-center mb-3 shadow-sm position-relative", color="primary", inverse=True
                ), width=4
            ) for _, row in yearly_summary.iterrows()
        ]

        # Create the bar chart figure for monthly income
        colors = ['#4682B4', '#5F9EA0', '#66CDAA']  # Slightly varying colors for different years
        fig = go.Figure(
            data=[
                go.Bar(
                    x=summary_df['YearMonth'].astype(str),
                    y=summary_df['TotalIncome'],
                    text=summary_df['TotalIncome'],
                    textposition='auto',
                    marker_color=[colors[year % len(colors)] for year in summary_df['YearMonth'].dt.year],
                    hoverinfo='none'  # Disable hover information
                )
            ]
        )
        fig.update_layout(
            title='Monthly Income',
            xaxis_title='Month',
            yaxis_title='Total Income',
            template='plotly_white',
            showlegend=False,
            dragmode=False  # Disable drag interactions
        )
        fig.update_xaxes(fixedrange=True)  # Disable zooming on x-axis
        fig.update_yaxes(fixedrange=True)  # Disable zooming on y-axis

        return df.to_dict('records'), fig, yearly_income_boxes

    @app.callback(
        Output('student-summary-row', 'children'),
        Input('student-search', 'value')
    )
    def update_student_summary(student_name):
        if not student_name:
            return []

        df = fetch_data_from_sheets()
        student_df = df[df['Name:'].str.contains(student_name, case=False, na=False)]
        if student_df.empty:
            return [dbc.Col(html.Div("No data found for the entered student.", className="text-center text-danger"))]

        total_lessons = len(student_df)
        total_hours = student_df['Stunden:'].sum()
        first_lesson_date = student_df['Datum:'].min().strftime('%d.%m.%Y')
        last_lesson_date = student_df['Datum:'].max().strftime('%d.%m.%Y')
        total_income = student_df['Lohn:'].sum()

        student_summary = dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4(f"Student: {student_name}", className="card-title"),
                    html.H5(f"Total Lessons: {total_lessons}", className="card-text"),
                    html.H5(f"Total Hours: {total_hours}", className="card-text"),
                    html.H5(f"First Lesson Date: {first_lesson_date}", className="card-text"),
                    html.H5(f"Last Lesson Date: {last_lesson_date}", className="card-text"),
                    html.H5(f"Total Income: {total_income} €", className="card-text")
                ]),
                className="text-center"
            ), width=12
        )

        return [student_summary]

    @app.callback(
        Output({'type': 'collapse', 'index': dash.dependencies.MATCH}, 'is_open'),
        Input({'type': 'toggle-button', 'index': dash.dependencies.MATCH}, 'n_clicks'),
        State({'type': 'collapse', 'index': dash.dependencies.MATCH}, 'is_open')
    )
    def toggle_collapse(n_clicks, is_open):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        if n_clicks:
            return not is_open
        return is_open

    import plotly.express as px

    @app.callback(
    Output('top-10-students-graph', 'figure'),
    Input('refresh-button', 'n_clicks')
    )
    def update_top_10_students(n_clicks):
        df = fetch_data_from_sheets()
        top_students = df.groupby('Name:')['Lohn:'].sum().sort_values(ascending=False).head(10).reset_index()
        
        fig = go.Figure(
            data=[
                go.Bar(
                    x=top_students['Name:'],
                    y=top_students['Lohn:'],
                    text=top_students['Lohn:'],
                    textposition='auto',
                    marker_color='#4682B4'
                )
            ]
        )
        fig.update_layout(
            title='Top 10 Students by Money Spent',
            xaxis_title='Student Name',
            yaxis_title='Total Money Spent (€)',
            template='plotly_white',
            showlegend=False
        )
        return fig

    @app.callback(
        Output('total-summary-row', 'children'),
        Input('refresh-button', 'n_clicks')
    )
    def update_total_summary(n_clicks):
        df = fetch_data_from_sheets()

        # Calculate total hours taught and total income
        total_hours = df['Stunden:'].sum()
        total_income = df['Lohn:'].sum()

        # Create summary card
        total_summary_card = dbc.Card(
            dbc.CardBody([
                html.H4("Total Summary", className="card-title"),
                html.H5(f"Total Hours Taught: {total_hours:.2f} Hours", className="card-text"),
                html.H5(f"Total Income Earned: {total_income:.2f} €", className="card-text")
            ]),
            className="text-center mb-4 shadow-sm"
        )

        return [dbc.Col(total_summary_card, width=12)]


# Add graph to layout
