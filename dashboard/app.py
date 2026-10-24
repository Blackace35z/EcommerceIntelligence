
from pathlib import Path
import calendar

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

# =========================================================
# 1. DATA
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "online_retail_cleaned.csv"

df = pd.read_csv(DATA_PATH, parse_dates=["InvoiceDate"])

df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="coerce"
)

df = df.dropna(subset=["InvoiceDate"]).copy()

# Convert cancellation flag safely.
cancellation_flag = df["IsCancellationInvoice"]

if cancellation_flag.dtype == object:
    cancellation_flag = (
        cancellation_flag.astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False})
        .fillna(False)
    )
else:
    cancellation_flag = (
        cancellation_flag.fillna(False).astype(bool)
    )

# Provisional positive-sales definition.
is_positive_sale = (
    (~cancellation_flag)
    & (df["Quantity"] > 0)
    & (df["UnitPrice"] > 0)
)

df["SalesValue"] = (
    df["Quantity"] * df["UnitPrice"]
).where(is_positive_sale, 0.0)

# Month key for monthly aggregations.
df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)

MIN_DATE = df["InvoiceDate"].min().date()
MAX_DATE = df["InvoiceDate"].max().date()

ALL_COUNTRIES = sorted(df["Country"].dropna().unique())

app = Dash(__name__)
app.title = "E-commerce Intelligence"

# =========================================================
# 2. DESIGN CONSTANTS
# =========================================================

BG = "#0B1020"
PANEL = "#121A2B"
BORDER = "#263249"
TEXT = "#F3F6FC"
MUTED = "#93A4BD"
ACCENT = "#7C9CFF"
GREEN = "#39D6A0"
RED = "#FF7185"

GRAPH_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}

# =========================================================
# 3. REUSABLE COMPONENTS
# =========================================================

def make_kpi(
    title,
    value,
    subtitle,
    icon,
    positive=False,
    negative=False,
):
    """Build a styled KPI card."""

    subtitle_class = "kpi-subtitle"

    if positive:
        subtitle_class += " kpi-positive"

    if negative:
        subtitle_class += " kpi-negative"

    return html.Div(
        className="kpi-card",
        children=[
            html.Div(
                className="kpi-top",
                children=[
                    html.Div(title, className="kpi-label"),
                    html.Div(icon, className="kpi-icon"),
                ],
            ),
            html.Div(
                value,
                className="kpi-value",
            ),
            html.Div(
                subtitle,
                className=subtitle_class,
            ),
        ],
    )


def style_chart(fig):
    """Apply the dashboard's consistent chart theme."""

    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font={
            "color": TEXT,
            "family": "Inter, Segoe UI, Arial",
            "size": 11,
        },
        margin={
            "l": 16,
            "r": 16,
            "t": 16,
            "b": 16,
        },
        coloraxis_showscale=False,
        hoverlabel={
            "bgcolor": "#1B2740",
            "font_color": TEXT,
            "bordercolor": BORDER,
            "font_family": "Inter, Segoe UI, Arial",
        },
        xaxis={
            "gridcolor": BORDER,
            "zerolinecolor": BORDER,
            "showline": False,
            "tickfont": {"color": MUTED, "size": 10},
        },
        yaxis={
            "gridcolor": BORDER,
            "zerolinecolor": BORDER,
            "showline": False,
            "tickfont": {"color": MUTED, "size": 10},
        },
        legend={
            "font": {"color": MUTED},
        },
    )

    return fig


def money(value):
    """Format a value as British pounds."""

    return f"£{value:,.0f}"


def empty_chart(message):
    """Create an attractive empty chart when no data matches."""

    fig = px.scatter()

    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {
                    "color": MUTED,
                    "size": 14,
                },
            }
        ],
        margin={"l": 16, "r": 16, "t": 16, "b": 16},
    )

    return fig


def get_complete_months(start, end):
    """
    Return complete calendar months fully covered by:
    - The dataset's global date boundaries
    - The selected dashboard date range

    A month is complete only when the entire calendar
    month is covered.
    """

    start = pd.Timestamp(start).normalize()
    end = pd.Timestamp(end).normalize()

    dataset_start = pd.Timestamp(MIN_DATE).normalize()
    dataset_end = pd.Timestamp(MAX_DATE).normalize()

    eligible_months = []

    first_month = start.to_period("M")
    last_month = end.to_period("M")

    for month in pd.period_range(
        first_month,
        last_month,
        freq="M",
    ):
        month_start = month.start_time.normalize()

        month_end = pd.Timestamp(
            year=month.year,
            month=month.month,
            day=calendar.monthrange(month.year, month.month)[1],
        )

        # The month must be fully inside the dataset.
        if month_start < dataset_start:
            continue

        if month_end > dataset_end:
            continue

        # The month must also be fully inside the selection.
        if month_start < start:
            continue

        if month_end > end:
            continue

        eligible_months.append(str(month))

    return eligible_months


def calculate_monthly_growth(filtered, start, end):
    """
    Compare the two most recent complete months.

    Returns:
        growth_value, subtitle, growth_percentage
    """

    eligible_months = get_complete_months(start, end)

    if len(eligible_months) < 2:
        return (
            "N/A",
            "Select at least two complete months",
            None,
        )

    previous_month = eligible_months[-2]
    current_month = eligible_months[-1]

    monthly_sales = (
        filtered[
            filtered["Month"].isin(
                [previous_month, current_month]
            )
        ]
        .groupby("Month")["SalesValue"]
        .sum()
    )

    previous_sales = float(
        monthly_sales.get(previous_month, 0.0)
    )

    current_sales = float(
        monthly_sales.get(current_month, 0.0)
    )

    comparison_label = (
        f"{previous_month} → {current_month}"
    )

    if previous_sales <= 0:
        return (
            "N/A",
            f"No previous-month sales · {previous_month}",
            None,
        )

    growth = (
        (current_sales - previous_sales)
        / previous_sales
    ) * 100

    if growth > 0:
        growth_value = f"+{growth:.1f}%"
    else:
        growth_value = f"{growth:.1f}%"

    return growth_value, comparison_label, growth


# =========================================================
# 4. SIDEBAR
# =========================================================

sidebar = html.Aside(
    className="sidebar",
    children=[
        html.Div(
            className="brand",
            children=[
                html.Div("E", className="brand-logo"),
                html.Div(
                    children=[
                        html.Div(
                            "E-commerce",
                            className="brand-name",
                        ),
                        html.Div(
                            "INTELLIGENCE",
                            className="brand-subtitle",
                        ),
                    ]
                ),
            ],
        ),

        html.Div(
            "WORKSPACE",
            className="sidebar-label",
        ),

        html.Nav(
            className="sidebar-nav",
            children=[
                html.A(
                    href="#overview",
                    className="nav-link active",
                    children=[
                        html.Span("◫", className="nav-icon"),
                        html.Span("Overview"),
                    ],
                ),
                html.A(
                    href="#sales",
                    className="nav-link",
                    children=[
                        html.Span("↗", className="nav-icon"),
                        html.Span("Sales analytics"),
                    ],
                ),
                html.A(
                    href="#products",
                    className="nav-link",
                    children=[
                        html.Span("▦", className="nav-icon"),
                        html.Span("Product insights"),
                    ],
                ),
                html.A(
                    href="#filters",
                    className="nav-link",
                    children=[
                        html.Span("☷", className="nav-icon"),
                        html.Span("Filters"),
                    ],
                ),
            ],
        ),

        html.Div(className="sidebar-spacer"),

        html.Div(
            className="sidebar-footer",
            children=[
                html.Div(
                    children=[
                        html.Span(className="status-dot"),
                        html.Span("Analytics system"),
                    ],
                    className="sidebar-footer-title",
                ),
                html.Div(
                    "Online Retail dataset · 2010–2011",
                    className="sidebar-footer-text",
                ),
                html.Div(
                    "Built with Python, Dash and Plotly",
                    className="sidebar-footer-text",
                ),
            ],
        ),
    ],
)

# =========================================================
# 5. FILTER COMPONENTS
# =========================================================

country_dropdown = dcc.Dropdown(
    id="country-filter",
    options=[
        {
            "label": "All countries",
            "value": "ALL",
        }
    ] + [
        {
            "label": country,
            "value": country,
        }
        for country in ALL_COUNTRIES
    ],
    value="ALL",
    clearable=False,
)

start_date_picker = dcc.DatePickerSingle(
    id="start-date",
    min_date_allowed=MIN_DATE,
    max_date_allowed=MAX_DATE,
    date=MIN_DATE,
    display_format="DD MMM YYYY",
    clearable=False,
)

end_date_picker = dcc.DatePickerSingle(
    id="end-date",
    min_date_allowed=MIN_DATE,
    max_date_allowed=MAX_DATE,
    date=MAX_DATE,
    display_format="DD MMM YYYY",
    clearable=False,
)

quick_range_dropdown = dcc.Dropdown(
    id="quick-range",
    options=[
        {"label": "Entire period", "value": "ALL"},
        {"label": "Last 30 days", "value": "30D"},
        {"label": "Last 90 days", "value": "90D"},
        {"label": "Last 6 months", "value": "6M"},
        {"label": "Last 12 months", "value": "12M"},
    ],
    value="ALL",
    clearable=False,
)

# =========================================================
# 6. DASHBOARD LAYOUT
# =========================================================

app.layout = html.Div(
    className="app-shell",
    children=[
        sidebar,

        html.Main(
            className="main-content",
            children=[
                html.Div(
                    className="page-container",

                    children=[
                        # ---------------------------------
                        # Header
                        # ---------------------------------

                        html.Header(
                            id="overview",
                            className="page-header",
                            children=[
                                html.Div(
                                    children=[
                                        html.Div(
                                            "ECOMMERCE / ANALYTICS",
                                            className="page-eyebrow",
                                        ),
                                        html.H1(
                                            "E-commerce Intelligence",
                                            className="page-title",
                                        ),
                                        html.P(
                                            "Understand your sales, markets "
                                            "and product performance.",
                                            className="page-description",
                                        ),
                                    ]
                                ),

                                html.Div(
                                    className="header-right",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.Span(
                                                    className="status-dot"
                                                ),
                                                html.Span(
                                                    "Dataset loaded"
                                                ),
                                            ],
                                            className="header-badge",
                                        ),
                                    ],
                                ),
                            ],
                        ),

                        # ---------------------------------
                        # Filters
                        # ---------------------------------

                        html.Section(
                            id="filters",
                            className="filter-panel",
                            children=[
                                html.Div(
                                    className="filter-heading",
                                    children=[
                                        html.Div(
                                            "⌘",
                                            className="filter-heading-icon",
                                        ),
                                        html.Span("Dashboard filters"),
                                    ],
                                ),

                                html.Div(
                                    className="filter-grid",
                                    children=[
                                        html.Div(
                                            className="filter-field",
                                            children=[
                                                html.Label(
                                                    "MARKET",
                                                    className="filter-label",
                                                ),
                                                country_dropdown,
                                            ],
                                        ),

                                        html.Div(
                                            className="filter-field",
                                            children=[
                                                html.Label(
                                                    "START DATE",
                                                    className="filter-label",
                                                ),
                                                start_date_picker,
                                            ],
                                        ),

                                        html.Div(
                                            className="filter-field",
                                            children=[
                                                html.Label(
                                                    "END DATE",
                                                    className="filter-label",
                                                ),
                                                end_date_picker,
                                            ],
                                        ),

                                        html.Div(
                                            className="filter-field",
                                            children=[
                                                html.Label(
                                                    "QUICK RANGE",
                                                    className="filter-label",
                                                ),
                                                quick_range_dropdown,
                                            ],
                                        ),
                                    ],
                                ),

                                html.Div(
                                    id="filter-status",
                                    className="filter-status",
                                ),
                            ],
                        ),

                        # ---------------------------------
                        # KPI Section
                        # ---------------------------------

                        html.Section(
                            className="performance-section",
                            children=[
                                html.Div(
                                    className="section-heading",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.H2(
                                                    "Performance overview",
                                                    className="section-title",
                                                ),
                                                html.P(
                                                    "Key metrics for the selected period",
                                                    className="section-description",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            "LIVE FILTERS",
                                            className="section-tag",
                                        ),
                                    ],
                                ),

                                html.Div(
                                    id="kpi-cards",
                                    className="kpi-grid",
                                ),
                            ],
                        ),

                        # ---------------------------------
                        # Sales Analytics
                        # ---------------------------------

                        html.Section(
                            id="sales",
                            children=[
                                html.Div(
                                    className="section-heading",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.H2(
                                                    "Sales analytics",
                                                    className="section-title",
                                                ),
                                                html.P(
                                                    "Track sales over time and compare markets",
                                                    className="section-description",
                                                ),
                                            ]
                                        ),
                                    ],
                                ),

                                html.Div(
                                    className="chart-grid",
                                    children=[
                                        # Monthly sales chart
                                        html.Div(
                                            className="chart-card",
                                            children=[
                                                html.Div(
                                                    className="chart-header",
                                                    children=[
                                                        html.Div(
                                                            children=[
                                                                html.H3(
                                                                    "Monthly sales trend",
                                                                    className="chart-title",
                                                                ),
                                                                html.Div(
                                                                    "Sales value by month",
                                                                    className="chart-subtitle",
                                                                ),
                                                            ]
                                                        ),
                                                        html.Div(
                                                            "TREND",
                                                            className="chart-tag",
                                                        ),
                                                    ],
                                                ),

                                                dcc.Graph(
                                                    id="monthly-chart",
                                                    config=GRAPH_CONFIG,
                                                    style={
                                                        "height": "330px"
                                                    },
                                                ),
                                            ],
                                        ),

                                        # Country chart
                                        html.Div(
                                            className="chart-card",
                                            children=[
                                                html.Div(
                                                    className="chart-header",
                                                    children=[
                                                        html.Div(
                                                            children=[
                                                                html.H3(
                                                                    "Top countries",
                                                                    className="chart-title",
                                                                ),
                                                                html.Div(
                                                                    "Markets ranked by sales value",
                                                                    className="chart-subtitle",
                                                                ),
                                                            ]
                                                        ),
                                                        html.Div(
                                                            "MARKETS",
                                                            className="chart-tag",
                                                        ),
                                                    ],
                                                ),

                                                dcc.Graph(
                                                    id="country-chart",
                                                    config=GRAPH_CONFIG,
                                                    style={
                                                        "height": "330px"
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),

                        # ---------------------------------
                        # Product Insights
                        # ---------------------------------

                        html.Section(
                            id="products",
                            children=[
                                html.Div(
                                    className="section-heading",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.H2(
                                                    "Product insights",
                                                    className="section-title",
                                                ),
                                                html.P(
                                                    "Products ranked by positive sales value",
                                                    className="section-description",
                                                ),
                                            ]
                                        ),
                                    ],
                                ),

                                html.Div(
                                    className="chart-card",
                                    children=[
                                        html.Div(
                                            className="chart-header",
                                            children=[
                                                html.Div(
                                                    children=[
                                                        html.H3(
                                                            "Top 10 products",
                                                            className="chart-title",
                                                        ),
                                                        html.Div(
                                                            "Highest-value product descriptions",
                                                            className="chart-subtitle",
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    "PRODUCTS",
                                                    className="chart-tag",
                                                ),
                                            ],
                                        ),

                                        dcc.Graph(
                                            id="product-chart",
                                            config=GRAPH_CONFIG,
                                            style={
                                                "height": "420px"
                                            },
                                        ),
                                    ],
                                ),
                            ],
                        ),

                        # ---------------------------------
                        # Metric Note
                        # ---------------------------------

                        html.Div(
                            className="insight-panel",
                            children=[
                                html.Div(
                                    "i",
                                    className="insight-icon",
                                ),

                                html.Div(
                                    children=[
                                        html.Div(
                                            "About these metrics",
                                            className="insight-title",
                                        ),
                                        html.Div(
                                            "Sales value includes only positive-quantity, "
                                            "positive-price lines on non-cancellation "
                                            "invoices. Returns and accounting adjustments "
                                            "are not fully reconciled, so these values "
                                            "are provisional rather than audited net revenue. "
                                            "Monthly growth compares the two most recent "
                                            "complete calendar months available within "
                                            "the selected date range. Completeness is "
                                            "determined using the dataset's global date "
                                            "boundaries. December 2011 contains data "
                                            "only through December 9.",
                                            className="insight-text",
                                        ),
                                    ]
                                ),
                            ],
                        ),

                        # ---------------------------------
                        # Footer
                        # ---------------------------------

                        html.Footer(
                            className="dashboard-footer",
                            children=[
                                html.Div(
                                    children=[
                                        html.Span(
                                            "E-commerce Intelligence",
                                            className="footer-brand",
                                        ),
                                        html.Span(
                                            " · Data analytics project"
                                        ),
                                    ]
                                ),
                                html.Div(
                                    "Python · Pandas · Dash · Plotly"
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# =========================================================
# 7. CALLBACK: FILTERS, KPIs AND CHARTS
# =========================================================

@app.callback(
    Output("kpi-cards", "children"),
    Output("monthly-chart", "figure"),
    Output("country-chart", "figure"),
    Output("product-chart", "figure"),
    Output("filter-status", "children"),
    Input("country-filter", "value"),
    Input("start-date", "date"),
    Input("end-date", "date"),
    Input("quick-range", "value"),
)
def update_dashboard(
    selected_country,
    start_date,
    end_date,
    quick_range,
):
    filtered = df

    # ---------------------------------------------
    # Filter by country
    # ---------------------------------------------

    if selected_country and selected_country != "ALL":
        filtered = filtered[
            filtered["Country"] == selected_country
        ]

    # ---------------------------------------------
    # Date selection
    # ---------------------------------------------

    start = (
        pd.Timestamp(start_date).normalize()
        if start_date
        else pd.Timestamp(MIN_DATE)
    )

    end = (
        pd.Timestamp(end_date).normalize()
        if end_date
        else pd.Timestamp(MAX_DATE)
    )

    # Quick ranges use the latest dataset date.
    if quick_range and quick_range != "ALL":
        days_by_range = {
            "30D": 30,
            "90D": 90,
            "6M": 183,
            "12M": 365,
        }

        days = days_by_range.get(quick_range)

        if days:
            end = pd.Timestamp(MAX_DATE).normalize()

            start = max(
                pd.Timestamp(MIN_DATE).normalize(),
                end - pd.Timedelta(days=days - 1),
            )

    # ---------------------------------------------
    # Apply dates
    # ---------------------------------------------

    if start > end:
        filtered = filtered.iloc[0:0]

        status = (
            "Start date must be on or before the end date."
        )

    else:
        filtered = filtered[
            (filtered["InvoiceDate"] >= start)
            & (
                filtered["InvoiceDate"]
                < end + pd.Timedelta(days=1)
            )
        ]

        status = (
            f"Showing {start.strftime('%d %b %Y')} – "
            f"{end.strftime('%d %b %Y')} "
            f"· {len(filtered):,} transaction lines"
        )

        if selected_country and selected_country != "ALL":
            status += f" · Market: {selected_country}"

    # =================================================
    # KPI CALCULATIONS
    # =================================================

    sales_total = float(filtered["SalesValue"].sum())

    invoice_count = filtered.loc[
        filtered["SalesValue"] > 0,
        "InvoiceNo",
    ].nunique()

    customer_count = filtered["CustomerID"].nunique()

    line_count = len(filtered)

    # Average Order Value.
    aov = (
        sales_total / invoice_count
        if invoice_count > 0
        else 0.0
    )

    # Monthly sales growth.
    growth_value, growth_subtitle, monthly_growth = (
        calculate_monthly_growth(
            filtered,
            start,
            end,
        )
    )

    growth_positive = (
        monthly_growth is not None
        and monthly_growth >= 0
    )

    growth_negative = (
        monthly_growth is not None
        and monthly_growth < 0
    )

    kpis = [
        make_kpi(
            "POSITIVE SALES VALUE",
            money(sales_total),
            "Provisional · GBP (£)",
            "£",
            positive=True,
        ),

        make_kpi(
            "INVOICES WITH SALES",
            f"{invoice_count:,}",
            "Invoices with positive sales lines",
            "▤",
        ),

        make_kpi(
            "AVERAGE ORDER VALUE",
            f"£{aov:,.2f}",
            "Positive sales value per invoice",
            "↗",
            positive=True,
        ),

        make_kpi(
            "MONTHLY SALES GROWTH",
            growth_value,
            growth_subtitle,
            "↗",
            positive=growth_positive,
            negative=growth_negative,
        ),

        make_kpi(
            "IDENTIFIABLE CUSTOMERS",
            f"{customer_count:,}",
            "Customers with a recorded ID",
            "♙",
        ),

        make_kpi(
            "TRANSACTION LINES",
            f"{line_count:,}",
            "Rows matching the selected filters",
            "▦",
        ),
    ]

    # =================================================
    # CHART 1: MONTHLY SALES
    # =================================================

    monthly = (
        filtered.groupby(
            "Month",
            as_index=False,
        )["SalesValue"]
        .sum()
        .sort_values("Month")
    )

    if monthly.empty:
        monthly_fig = empty_chart(
            "No sales data for the selected filters"
        )

    else:
        monthly_fig = px.line(
            monthly,
            x="Month",
            y="SalesValue",
            markers=True,
        )

        monthly_fig.update_traces(
            line={
                "color": ACCENT,
                "width": 3,
            },
            marker={
                "size": 7,
                "color": ACCENT,
                "line": {
                    "width": 2,
                    "color": PANEL,
                },
            },
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Sales: £%{y:,.2f}"
                "<extra></extra>"
            ),
        )

        monthly_fig.update_xaxes(
            title=None,
            tickangle=-30,
        )

        monthly_fig.update_yaxes(
            title=None,
            tickformat="£,.0f",
        )

        style_chart(monthly_fig)

    # =================================================
    # CHART 2: TOP COUNTRIES
    # =================================================

    country_summary = (
        filtered.groupby(
            "Country",
            as_index=False,
        )["SalesValue"]
        .sum()
        .sort_values(
            "SalesValue",
            ascending=False,
        )
        .head(10)
        .sort_values(
            "SalesValue",
            ascending=True,
        )
    )

    country_summary = country_summary[
        country_summary["SalesValue"] > 0
    ]

    if country_summary.empty:
        country_fig = empty_chart(
            "No country sales data available"
        )

    else:
        country_fig = px.bar(
            country_summary,
            x="SalesValue",
            y="Country",
            orientation="h",
            color="SalesValue",
            color_continuous_scale=[
                "#263B65",
                ACCENT,
            ],
        )

        country_fig.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Sales: £%{x:,.2f}"
                "<extra></extra>"
            )
        )

        country_fig.update_xaxes(
            title=None,
            tickformat="£,.0f",
        )

        country_fig.update_yaxes(title=None)

        style_chart(country_fig)

    # =================================================
    # CHART 3: TOP PRODUCTS
    # =================================================

    product_summary = (
        filtered.loc[
            filtered["SalesValue"] > 0
        ]
        .groupby(
            "Description",
            as_index=False,
        )["SalesValue"]
        .sum()
    )

    non_merchandise_terms = (
        "POSTAGE",
        "DOTCOM POSTAGE",
        "MANUAL",
        "DISCOUNT",
        "ADJUST BAD DEBT",
    )

    product_summary = product_summary[
        ~product_summary["Description"]
        .fillna("")
        .str.upper()
        .apply(
            lambda value: any(
                term in value
                for term in non_merchandise_terms
            )
        )
    ]

    product_summary = (
        product_summary.nlargest(
            10,
            "SalesValue",
        )
        .sort_values(
            "SalesValue",
            ascending=True,
        )
    )

    if product_summary.empty:
        product_fig = empty_chart(
            "No product sales data available"
        )

    else:
        product_fig = px.bar(
            product_summary,
            x="SalesValue",
            y="Description",
            orientation="h",
            color="SalesValue",
            color_continuous_scale=[
                "#263B65",
                GREEN,
            ],
        )

        product_fig.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Sales: £%{x:,.2f}"
                "<extra></extra>"
            )
        )

        product_fig.update_xaxes(
            title=None,
            tickformat="£,.0f",
        )

        product_fig.update_yaxes(title=None)

        style_chart(product_fig)

    # =================================================
    # RETURN DASHBOARD COMPONENTS
    # =================================================

    return (
        kpis,
        monthly_fig,
        country_fig,
        product_fig,
        status,
    )


# =========================================================
# 8. START SERVER
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
