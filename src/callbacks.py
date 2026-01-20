"""Callback handlers for Dash application."""
import logging
from typing import List, Tuple, Optional
from datetime import datetime

import dash
import plotly.graph_objs as go
import pandas as pd
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from .data_handler import SheetsDataHandler
from .config import Config

logger = logging.getLogger(__name__)


class DashboardCallbacks:
    """Manages all dashboard callbacks."""

    def __init__(self, app, data_handler: SheetsDataHandler = None, config: Config = None):
        """Initialize callbacks.
        
        Args:
            app: Dash application instance.
            data_handler: SheetsDataHandler instance. Creates new if None.
            config: Configuration object.
        """
        self.app = app
        self.config = config or Config()
        self.data_handler = data_handler or SheetsDataHandler(config)
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Register all callbacks with the Dash app."""
        self._setup_refresh_callback()
        self._setup_student_search_callback()
        self._setup_collapse_toggle_callback()
        self._setup_top_students_callback()
        self._setup_total_summary_callback()
        self._setup_key_metrics_callback()

    def _resolve_date_range(
        self, quick_range: Optional[str], start_date: Optional[str], end_date: Optional[str]
    ) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """Compute start/end timestamps from quick preset or manual selection."""
        today = pd.Timestamp.now().normalize()

        if quick_range == "last30":
            return today - pd.Timedelta(days=30), today
        if quick_range == "last90":
            return today - pd.Timedelta(days=90), today
        if quick_range == "ytd":
            return pd.Timestamp(year=today.year, month=1, day=1), today
        if quick_range == "all":
            return None, None

        # Fallback to manual range
        start_ts = pd.to_datetime(start_date).normalize() if start_date else None
        end_ts = pd.to_datetime(end_date).normalize() if end_date else None
        return start_ts, end_ts

    def _filter_df_by_range(
        self, df, quick_range: Optional[str], start_date: Optional[str], end_date: Optional[str]
    ):
        """Apply date range filtering to the DataFrame."""
        start_ts, end_ts = self._resolve_date_range(quick_range, start_date, end_date)
        return self.data_handler.filter_by_date(df, start_ts, end_ts)

    def _setup_refresh_callback(self):
        """Setup data refresh and chart update callbacks."""

        @self.app.callback(
            [
                Output("data-table", "data"),
                Output("monthly-income-graph", "figure"),
                Output("yearly-income-summary-row", "children"),
            ],
            [
                Input("refresh-button", "n_clicks"),
                Input("quick-range", "value"),
                Input("date-range", "start_date"),
                Input("date-range", "end_date"),
            ],
        )
        def refresh_data(n_clicks, quick_range, start_date, end_date):
            """Refresh all data and update dashboard."""
            try:
                df = self.data_handler.fetch_data()
                filtered_df = self._filter_df_by_range(df, quick_range, start_date, end_date)

                summary_df = self.data_handler.get_monthly_summary(filtered_df)
                yearly_summary = self.data_handler.get_yearly_summary(filtered_df)

                yearly_income_boxes = self._create_yearly_cards(yearly_summary)
                monthly_fig = self._create_monthly_chart(summary_df)

                return filtered_df.to_dict("records"), monthly_fig, yearly_income_boxes
            except Exception as e:
                logger.error(f"Error in refresh_data callback: {e}")
                return [], {}, [html.Div("Error loading data", className="text-danger")]

        return refresh_data

    def _create_yearly_cards(self, yearly_summary) -> List:
        """Create yearly summary cards.
        
        Args:
            yearly_summary: DataFrame with yearly data.
            
        Returns:
            List of dbc.Col components containing cards.
        """
        cards = []
        for _, row in yearly_summary.iterrows():
            card = dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(f"Year: {int(row['Year'])}", className="card-title"),
                                html.H5(
                                    f"Total Income: {row['TotalIncome']:.2f} €",
                                    className="card-text",
                                ),
                            ]
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        f"Students: {int(row['NumStudents'])}",
                                        className="card-text",
                                    ),
                                    html.H5(
                                        f"Avg Monthly: {row['AvgMonthlyIncome']:.2f} €",
                                        className="card-text",
                                    ),
                                    html.H5(
                                        f"Avg Hourly: {row['AvgMonthlyWage']:.2f} €",
                                        className="card-text",
                                    ),
                                    html.H5(
                                        f"Avg Hours/Month: {row['AvgMonthlyHours']:.2f}",
                                        className="card-text",
                                    ),
                                    html.H5(
                                        f"YoY Income: {row['YoYAvgMonthlyIncome']}",
                                        className="card-text",
                                    ),
                                    html.H5(
                                        f"YoY Hours: {row['YoYAvgMonthlyHours']}",
                                        className="card-text",
                                    ),
                                ]
                            ),
                            id={"type": "collapse", "index": int(row["Year"])},
                            is_open=False,
                        ),
                        dbc.Button(
                            html.I(className="bi bi-chevron-down"),
                            id={"type": "toggle-button", "index": int(row["Year"])},
                            color="link",
                            n_clicks=0,
                            style={
                                "position": "absolute",
                                "top": "5px",
                                "right": "10px",
                                "fontSize": "1.5em",
                                "color": "white",
                            },
                        ),
                    ],
                    className="text-center mb-3 shadow-sm position-relative",
                    color="primary",
                    inverse=True,
                ),
                width=4,
            )
            cards.append(card)
        return cards

    def _create_monthly_chart(self, summary_df) -> go.Figure:
        """Create monthly income bar chart.
        
        Args:
            summary_df: DataFrame with monthly aggregations.
            
        Returns:
            Plotly Figure object.
        """
        if summary_df.empty:
            return go.Figure().add_annotation(text="No data available")

        colorscale = ["#3a86ff", "#6dd3ff", "#ff6b6b"]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=summary_df["YearMonth"].astype(str),
                    y=summary_df["TotalIncome"],
                    text=summary_df["TotalIncome"].apply(lambda x: f"€{x:.2f}"),
                    textposition="outside",
                    marker=dict(
                        color=summary_df["TotalIncome"],
                        colorscale=colorscale,
                        line=dict(color="#0b132b", width=1),
                    ),
                    hovertemplate="<b>%{x}</b><br>Income: €%{y:.2f}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            title="Monthly Income",
            xaxis_title="Month",
            yaxis_title="Total Income (€)",
            template="plotly_white",
            showlegend=False,
            dragmode=False,
            height=420,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="Space Grotesk, sans-serif", size=13, color="#0b132b"),
            margin=dict(l=30, r=20, t=50, b=60),
        )
        fig.update_xaxes(fixedrange=True, showgrid=False)
        fig.update_yaxes(fixedrange=True, gridcolor="#eef2f8", zeroline=False)
        return fig

    def _setup_student_search_callback(self):
        """Setup student search callback."""

        @self.app.callback(
            Output("student-summary-row", "children"),
            [
                Input("student-search", "value"),
                Input("quick-range", "value"),
                Input("date-range", "start_date"),
                Input("date-range", "end_date"),
            ],
        )
        def update_student_summary(student_name: str, quick_range, start_date, end_date):
            """Update student summary based on search input."""
            if not student_name or len(student_name.strip()) == 0:
                return []

            try:
                df = self.data_handler.fetch_data()
                filtered_df = self._filter_df_by_range(df, quick_range, start_date, end_date)
                student_df = self.data_handler.get_student_summary(student_name, filtered_df)

                if student_df is None or student_df.empty:
                    return [
                        dbc.Col(
                            html.Div(
                                "No data found for the entered student.",
                                className="text-center text-danger",
                            )
                        )
                    ]

                total_lessons = len(student_df)
                total_hours = student_df["Stunden:"].sum()
                first_date = student_df["Datum:"].min().strftime("%d.%m.%Y")
                last_date = student_df["Datum:"].max().strftime("%d.%m.%Y")
                total_income = student_df["Lohn:"].sum()

                return [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(f"Student: {student_name}", className="card-title"),
                                    html.H5(f"Total Lessons: {total_lessons}", className="card-text"),
                                    html.H5(f"Total Hours: {total_hours:.2f}", className="card-text"),
                                    html.H5(f"First Lesson: {first_date}", className="card-text"),
                                    html.H5(f"Last Lesson: {last_date}", className="card-text"),
                                    html.H5(f"Total Income: {total_income:.2f} €", className="card-text"),
                                ]
                            ),
                            className="text-center",
                        ),
                        width=12,
                    )
                ]
            except Exception as e:
                logger.error(f"Error in student search: {e}")
                return [dbc.Col(html.Div("Error loading student data", className="text-danger"))]

    def _setup_collapse_toggle_callback(self):
        """Setup year card collapse toggle callback."""

        @self.app.callback(
            Output({"type": "collapse", "index": dash.dependencies.MATCH}, "is_open"),
            Input({"type": "toggle-button", "index": dash.dependencies.MATCH}, "n_clicks"),
            State({"type": "collapse", "index": dash.dependencies.MATCH}, "is_open"),
        )
        def toggle_collapse(n_clicks: int, is_open: bool) -> bool:
            """Toggle collapse state."""
            if n_clicks is None:
                raise dash.exceptions.PreventUpdate
            return not is_open if n_clicks else is_open

    def _setup_top_students_callback(self):
        """Setup top students chart callback."""

        @self.app.callback(
            Output("top-10-students-graph", "figure"),
            [
                Input("refresh-button", "n_clicks"),
                Input("quick-range", "value"),
                Input("date-range", "start_date"),
                Input("date-range", "end_date"),
            ],
        )
        def update_top_students(n_clicks, quick_range, start_date, end_date):
            """Update top students chart."""
            try:
                df = self.data_handler.fetch_data()
                filtered_df = self._filter_df_by_range(df, quick_range, start_date, end_date)
                top_students = self.data_handler.get_top_students(df=filtered_df)

                if top_students.empty:
                    return go.Figure().add_annotation(text="No data available")

                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=top_students["Name:"],
                            y=top_students["Lohn:"],
                            text=top_students["Lohn:"].apply(lambda x: f"€{x:.2f}"),
                            textposition="outside",
                            marker=dict(
                                color="#3a86ff",
                                line=dict(color="#0b132b", width=1),
                            ),
                            hovertemplate="<b>%{x}</b><br>Income: €%{y:.2f}<extra></extra>",
                        )
                    ]
                )
                fig.update_layout(
                    title=f"Top {self.config.TOP_STUDENTS_COUNT} Students by Income",
                    xaxis_title="Student Name",
                    yaxis_title="Total Income (€)",
                    template="plotly_white",
                    showlegend=False,
                    height=420,
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(family="Space Grotesk, sans-serif", size=13, color="#0b132b"),
                    margin=dict(l=30, r=20, t=50, b=90),
                )
                fig.update_xaxes(tickangle=-35, showgrid=False)
                fig.update_yaxes(gridcolor="#eef2f8", zeroline=False)
                return fig
            except Exception as e:
                logger.error(f"Error in top students callback: {e}")
                return go.Figure().add_annotation(text="Error loading data")

    def _setup_total_summary_callback(self):
        """Setup total summary callback."""

        @self.app.callback(
            Output("total-summary-row", "children"),
            [
                Input("refresh-button", "n_clicks"),
                Input("quick-range", "value"),
                Input("date-range", "start_date"),
                Input("date-range", "end_date"),
            ],
        )
        def update_total_summary(n_clicks, quick_range, start_date, end_date):
            """Update total statistics."""
            try:
                df = self.data_handler.fetch_data()
                filtered_df = self._filter_df_by_range(df, quick_range, start_date, end_date)
                stats = self.data_handler.get_total_stats(filtered_df)

                card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Total Summary", className="card-title"),
                            html.H5(
                                f"Total Hours Taught: {stats['total_hours']:.2f} Hours",
                                className="card-text",
                            ),
                            html.H5(
                                f"Total Income Earned: {stats['total_income']:.2f} €",
                                className="card-text",
                            ),
                        ]
                    ),
                    className="text-center mb-4 shadow-sm",
                )
                return [dbc.Col(card, width=12)]
            except Exception as e:
                logger.error(f"Error in total summary callback: {e}")
                return [dbc.Col(html.Div("Error loading summary", className="text-danger"))]

    def _setup_key_metrics_callback(self):
        """Setup key metrics overview callback."""
        
        @self.app.callback(
            Output("key-metrics-row", "children"),
            [
                Input("refresh-button", "n_clicks"),
                Input("quick-range", "value"),
                Input("date-range", "start_date"),
                Input("date-range", "end_date"),
            ],
        )
        def update_key_metrics(n_clicks, quick_range, start_date, end_date):
            """Update key performance metrics."""
            try:
                df = self.data_handler.fetch_data()
                filtered_df = self._filter_df_by_range(df, quick_range, start_date, end_date)
                metrics = self.data_handler.get_key_metrics(filtered_df)
                
                return [
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-currency-euro me-2"), "Total Revenue"], className="metric-label"),
                                html.H3(f"€{metrics['total_revenue']:.2f}", className="metric-value"),
                            ]),
                        ], className="metric-card"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-clock me-2"), "Total Hours"], className="metric-label"),
                                html.H3(f"{metrics['total_hours']:.1f}h", className="metric-value"),
                            ]),
                        ], className="metric-card"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-graph-up me-2"), "Avg Rate"], className="metric-label"),
                                html.H3(f"€{metrics['avg_hourly_rate']:.2f}/h", className="metric-value"),
                            ]),
                        ], className="metric-card"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-people me-2"), "Students"], className="metric-label"),
                                html.H3(f"{metrics['unique_students']}", className="metric-value"),
                            ]),
                        ], className="metric-card"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-calendar-event me-2"), "Sessions"], className="metric-label"),
                                html.H3(f"{metrics['total_sessions']}", className="metric-value"),
                            ]),
                        ], className="metric-card"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-hourglass-split me-2"), "Avg Session"], className="metric-label"),
                                html.H3(f"{metrics['avg_session_length']:.1f}h", className="metric-value"),
                            ]),
                        ], className="metric-card"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-calendar-month me-2"), "This Month Revenue"], className="metric-label"),
                                html.H3(f"€{metrics['this_month_revenue']:.2f}", className="metric-value"),
                            ]),
                        ], className="metric-card metric-card-highlight"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([html.I(className="bi bi-stopwatch me-2"), "This Month Hours"], className="metric-label"),
                                html.H3(f"{metrics['this_month_hours']:.1f}h", className="metric-value"),
                            ]),
                        ], className="metric-card metric-card-highlight"),
                    ], md=3, sm=6, xs=12, className="mb-3"),
                ]
            except Exception as e:
                logger.error(f"Error in key metrics callback: {e}")
                return [dbc.Col(html.Div("Error loading metrics", className="text-danger"))]
