"""Main Dash application for Tutoring Dashboard."""
import logging
from typing import List, Dict

import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

from .data_handler import SheetsDataHandler
from .callbacks import DashboardCallbacks
from .config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TutoringDashboardApp:
    """Main Tutoring Dashboard application class."""

    def __init__(self, config: Config = None):
        """Initialize the Tutoring Dashboard application.
        
        Args:
            config: Configuration object. Uses default Config if None.
        """
        self.config = config or Config()
        self.data_handler = SheetsDataHandler(self.config)
        self.app = self._create_app()
        self._setup_layout()
        self._setup_callbacks()

    def _create_app(self) -> dash.Dash:
        """Create and configure the Dash application.
        
        Returns:
            Configured Dash application instance.
        """
        external_stylesheets = [
            dbc.themes.BOOTSTRAP,
            "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.5.0/font/bootstrap-icons.min.css",
        ]
        return dash.Dash(__name__, external_stylesheets=external_stylesheets)

    def _setup_layout(self):
        """Setup the application layout."""
        try:
            df = self.data_handler.fetch_data()
            columns = [
                {"name": col, "id": col}
                for col in df.columns
                if col not in ["Anbieter", "Datum:", "Anfang:", "Ende:"]
            ]
        except Exception as e:
            logger.warning(f"Could not load initial data: {e}")
            columns = []

        self.app.layout = dbc.Container(
            [
                # Header Bar
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div([
                                html.H1("Tutoring Dashboard", className="header-title mb-0"),
                                html.P("Real-time insights", className="header-subtitle mb-0"),
                            ]),
                            md=6, xs=12,
                        ),
                        dbc.Col(
                            html.Div([
                                dbc.Button(
                                    [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                                    id="refresh-button", n_clicks=0, color="primary", size="sm", className="me-2",
                                ),
                                dbc.Badge("10s cache", color="light", text_color="dark", className="align-middle"),
                            ], className="d-flex justify-content-md-end justify-content-start align-items-center mt-3 mt-md-0"),
                            md=6, xs=12,
                        ),
                    ],
                    className="header-bar mb-4",
                ),

                # Key Metrics Overview
                dbc.Row(id="key-metrics-row", className="mb-4"),

                # Date Filters
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label("Quick filter", className="filter-label"),
                                                    dcc.Dropdown(
                                                        id="quick-range",
                                                        options=[
                                                            {"label": "Last 30 days", "value": "last30"},
                                                            {"label": "Last 90 days", "value": "last90"},
                                                            {"label": "Year to date", "value": "ytd"},
                                                            {"label": "All time", "value": "all"},
                                                            {"label": "Custom range", "value": "custom"},
                                                        ],
                                                        value="all",
                                                        clearable=False,
                                                    ),
                                                ],
                                                md=4, xs=12,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label("Custom date range", className="filter-label"),
                                                    dcc.DatePickerRange(
                                                        id="date-range",
                                                        display_format="DD.MM.YYYY",
                                                        clearable=True,
                                                    ),
                                                ],
                                                md=8, xs=12, className="mt-2 mt-md-0",
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            className="filter-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Yearly Income Summary
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(id="yearly-income-summary-row"),
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Total Summary
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(id="total-summary-row"),
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Student Search
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Search students", className="section-title"),
                                    dbc.Input(
                                        id="student-search",
                                        type="text",
                                        placeholder="Type a student name...",
                                        className="mb-2",
                                    ),
                                    html.Small("Tip: partial names work too", className="text-muted"),
                                ]
                            ),
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Student Summary
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(id="student-summary-row"),
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Top Students Chart
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Top earners"),
                                dbc.CardBody(dcc.Graph(id="top-10-students-graph")),
                            ],
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Monthly Income Chart
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Monthly income"),
                                dbc.CardBody(dcc.Graph(id="monthly-income-graph")),
                            ],
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),

                # Data Table
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Raw records"),
                                dbc.CardBody(
                                    dash_table.DataTable(
                                        id="data-table",
                                        columns=columns,
                                        data=[],
                                        page_size=self.config.PAGE_SIZE,
                                        filter_action="native",
                                        sort_action="native",
                                        style_table={"overflowX": "auto"},
                                        style_header={"backgroundColor": "#0b132b", "color": "white", "fontWeight": "600"},
                                        style_cell={"padding": "0.6rem", "fontSize": "14px"},
                                        style_data_conditional=[
                                            {"if": {"row_index": "odd"}, "backgroundColor": "#f7f9fc"},
                                        ],
                                    )
                                ),
                            ],
                            className="panel-card",
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),
            ],
            fluid=True,
            className="page-shell",
        )

    def _setup_callbacks(self):
        """Setup all dashboard callbacks."""
        DashboardCallbacks(self.app, self.data_handler, self.config)
        logger.info("Callbacks registered")

    def run(self, debug: bool = None, **kwargs):
        """Run the Dash application.
        
        Args:
            debug: Enable debug mode. Uses config default if None.
            **kwargs: Additional arguments to pass to app.run().
        """
        if debug is None:
            debug = self.config.DEBUG

        logger.info(f"Starting Tutoring Dashboard (debug={debug})")
        # Disable Flask reloader to avoid path issues when run.py lives one level up
        self.app.run(
            debug=debug,
            host=self.config.HOST,
            port=self.config.PORT,
            use_reloader=False,
            **kwargs,
        )


def create_app(config: Config = None) -> dash.Dash:
    """Factory function to create the Dash application.
    
    Args:
        config: Configuration object.
        
    Returns:
        Dash application instance.
    """
    app = TutoringDashboardApp(config)
    return app.app
