import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Financial Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Power BI-style CSS
st.markdown("""
<style>
    /* Hide Streamlit branding and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Dashboard title */
    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 1.5rem;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* KPI Card Styling */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
        max-width: 170px;
        min-width: 120px;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #3b82f6;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    }
    
    /* Metric styling for cards */
    .kpi-card [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #1f2937 !important;
        line-height: 1.2;
        margin-bottom: 0.5rem;
    }
    
    .kpi-card [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #6b7280 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    /* Chart containers */
    .stPlotlyChart {
        height: 250px !important;
    }
    
    /* Remove extra spacing */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Custom section dividers */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, #e2e8f0, #cbd5e1, #e2e8f0);
        border: none;
        margin: 1rem 0;
        border-radius: 2px;
    }
    
    /* Data table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px;
        color: #64748b;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


def format_currency_compact(value: float) -> str:
    """Return a compact currency string, rounded with no decimals ($12K, $5M)."""
    try:
        abs_value = abs(value)
        if abs_value < 1_000:
            return f"${value:,.0f}"
        for unit_value, unit_suffix in [
            (1_000_000_000_000, "T"),
            (1_000_000_000, "B"),
            (1_000_000, "M"),
            (1_000, "K"),
        ]:
            if abs_value >= unit_value:
                compact = value / unit_value
                return f"${compact:,.0f}{unit_suffix}"
        return f"${value:,.0f}"
    except Exception:
        return str(value)

@st.cache_data
def load_data():
    """Load and preprocess the CSV data"""
    try:
        # Load funding invoices
        invoices_df = pd.read_csv('funding_invoices.csv')
        
        # Load credit notes
        credit_notes_df = pd.read_csv('funding_invoice_credit_notes.csv')
        
        # Convert date columns
        date_columns_invoices = ['invoice_date', 'due_date', 'created', 'modified']
        for col in date_columns_invoices:
            if col in invoices_df.columns:
                invoices_df[col] = pd.to_datetime(invoices_df[col], errors='coerce')
        
        date_columns_credit = ['Date', 'created', 'modified']
        for col in date_columns_credit:
            if col in credit_notes_df.columns:
                credit_notes_df[col] = pd.to_datetime(credit_notes_df[col], errors='coerce')
        
        # Convert numeric columns
        numeric_columns_invoices = ['total', 'amount_paid', 'due_amount', 'gst', 'sub_total', 'total_hours', 'total_course_units']
        for col in numeric_columns_invoices:
            if col in invoices_df.columns:
                invoices_df[col] = pd.to_numeric(invoices_df[col], errors='coerce')
        
        numeric_columns_credit = ['Total', 'credit_amount', 'AppliedAmount', 'unapplied_amount']
        for col in numeric_columns_credit:
            if col in credit_notes_df.columns:
                credit_notes_df[col] = pd.to_numeric(credit_notes_df[col], errors='coerce')

        # Normalize/rename payment status values
        if 'payment_status' in invoices_df.columns:
            def normalize_payment_status(value: object) -> object:
                if pd.isna(value):
                    return value
                text = str(value).strip()
                key = text.upper()
                mapping = {
                    'P': 'Paid',
                    'PAID': 'Paid',
                    'U': 'Unpaid',
                    'UNPAID': 'Unpaid',
                    'PP': 'Partially Paid',
                    'PARTIALLY PAID': 'Partially Paid',
                    'CD': 'Closed',
                    'CLOSED': 'Closed',
                    
                }
                return mapping.get(key, text)

            invoices_df['payment_status'] = invoices_df['payment_status'].apply(normalize_payment_status)
        
        # Normalize/rename credit status values
        if 'credit_status' in credit_notes_df.columns:
            def normalize_credit_status(value: object) -> object:
                if pd.isna(value):
                    return value
                text = str(value).strip()
                key = text.upper() 
                mapping = {
                    'CR': 'Credit',
                    'CREDIT': 'Credit',
                    'CD': 'Closed',
                    'CLOSED': 'Closed',
                }
                return mapping.get(key, text)

            credit_notes_df['credit_status'] = credit_notes_df['credit_status'].apply(normalize_credit_status)
        
        return invoices_df, credit_notes_df
    
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        return None, None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

def calculate_key_metrics(invoices_df, credit_notes_df):
    """Calculate key financial metrics"""
    metrics = {}
    
    # Invoice metrics
    metrics['total_invoices'] = len(invoices_df)
    metrics['total_invoice_amount'] = round(invoices_df['total'].sum(), 2)
    metrics['total_amount_paid'] = round(invoices_df['amount_paid'].sum(), 2)
    metrics['total_outstanding'] = round(invoices_df['due_amount'].sum(), 2)
    metrics['avg_invoice_amount'] = round(invoices_df['total'].mean(), 2)
    
    # Credit note metrics
    metrics['total_credit_notes'] = len(credit_notes_df)
    metrics['total_credit_amount'] = round(credit_notes_df['Total'].sum(), 2)
    metrics['total_applied_credit'] = round(credit_notes_df['AppliedAmount'].sum(), 2)
    metrics['total_unapplied_credit'] = round(credit_notes_df['unapplied_amount'].sum(), 2)
    
    # Payment status analysis
    payment_status_counts = invoices_df['payment_status'].value_counts()
    metrics['payment_status_breakdown'] = payment_status_counts
    
    # Monthly trends
    invoices_df['invoice_month'] = invoices_df['invoice_date'].dt.to_period('M')
    monthly_invoices = invoices_df.groupby('invoice_month').agg({
        'total': 'sum',
        'amount_paid': 'sum',
        'id': 'count'
    }).reset_index()
    monthly_invoices['invoice_month'] = monthly_invoices['invoice_month'].astype(str)
    metrics['monthly_trends'] = monthly_invoices
    
    return metrics

def create_overview_charts(invoices_df, credit_notes_df, metrics):
    """Create overview charts for the dashboard"""
    # Payment Status Distribution - Compact donut chart
    payment_counts = invoices_df['payment_status'].value_counts()
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    
    fig_payment = go.Figure(data=[go.Pie(
        labels=payment_counts.index,
        values=payment_counts.values,
        hole=0.4,
        marker=dict(colors=colors[:len(payment_counts)], line=dict(color='#ffffff', width=2))
    )])
    
    fig_payment.update_traces(
        textposition='inside', 
        textinfo='percent',
        textfont_size=11,
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig_payment.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(t=40, b=40, l=20, r=20),
        height=250
    )
    
    # Yearly Invoice Trends - Compact line chart
    invoices_df['year'] = invoices_df['invoice_date'].dt.year
    yearly_data = invoices_df.groupby('year').agg({
        'total': 'sum',
        'invoice_number': 'count'
    }).reset_index()

    fig_trends = go.Figure()
    fig_trends.add_trace(go.Scatter(
        x=yearly_data['year'],
        y=yearly_data['total'],
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=6, color='#3b82f6'),
        fill='tonexty',
        fillcolor='rgba(59, 130, 246, 0.1)',
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>'
    ))

    fig_trends.update_layout(
        xaxis=dict(title="Year", tickangle=0, tickfont=dict(size=10), showgrid=False),
        yaxis=dict(title="Amount ($)", tickfont=dict(size=10), tickformat='$,.0f', showgrid=False),
        hovermode='x unified',
        showlegend=False,
        margin=dict(t=40, b=60, l=60, r=20),
        height=250
    )

    return fig_payment, fig_trends

def create_financial_analysis(invoices_df, credit_notes_df):
    """Create financial analysis charts"""
    # Top 10 Students by Invoice Amount - Compact horizontal bar
    top_students = invoices_df.groupby('display_name')['total'].sum().sort_values(ascending=False).head(10)
    
    fig_top_students = go.Figure(data=[go.Bar(
        x=top_students.values,
        y=top_students.index,
        orientation='h',
        marker=dict(
            color=top_students.values,
            colorscale='Blues',
            colorbar=dict(thickness=10, len=0.7)
        ),
        text=top_students.values,
        texttemplate='$%{text:,.0f}',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Total: $%{x:,.0f}<extra></extra>'
    )])
    
    fig_top_students.update_layout(
        xaxis=dict(title="Amount ($)", tickfont=dict(size=10), tickformat='$,.0f', showgrid=False),
        yaxis=dict(title="", tickfont=dict(size=9), showgrid=False),
        margin=dict(t=40, b=40, l=120, r=40),
        height=300,
        showlegend=False
    )
    
    # Invoice Amount Distribution - Compact histogram with data labels
    fig_amount_dist = go.Figure(data=[go.Histogram(
        x=invoices_df['total'],
        nbinsx=15,
        marker=dict(color='#3b82f6', opacity=0.7, line=dict(color='#1e40af', width=1)),
        hovertemplate='Range: $%{x}<br>Count: %{y}<extra></extra>',
        text=invoices_df['total'].value_counts(bins=15).values,
        texttemplate='%{text}',
        textposition='outside'
    )])
    
    fig_amount_dist.update_layout(
        xaxis=dict(title="Invoice Amount ($)", tickfont=dict(size=10), tickformat='$,.0f', showgrid=False),
        yaxis=dict(title="Count", tickfont=dict(size=10), showgrid=False),
        margin=dict(t=40, b=40, l=40, r=20),
        height=250,
        showlegend=False
    )
    
    # Payment Status vs Amount - Compact box plot
    fig_hours_amount = go.Figure()
    
    for status in invoices_df['payment_status'].unique():
        if pd.notna(status):
            data = invoices_df[invoices_df['payment_status'] == status]['total']
            fig_hours_amount.add_trace(go.Box(
                y=data,
                name=status,
                marker=dict(color='#3b82f6'),
                boxpoints='outliers',
                hovertemplate='<b>%{fullData.name}</b><br>Amount: $%{y:,.0f}<extra></extra>'
            ))
    
    fig_hours_amount.update_layout(
        xaxis=dict(title="Payment Status", tickfont=dict(size=10), showgrid=False),
        yaxis=dict(title="Amount ($)", tickfont=dict(size=10), tickformat='$,.0f', showgrid=False),
        margin=dict(t=40, b=40, l=60, r=20),
        height=250,
        showlegend=False
    )
    
    return fig_top_students, fig_amount_dist, fig_hours_amount

def create_credit_note_analysis(credit_notes_df):
    """Create credit note analysis charts"""
    
    # Credit Note Status Distribution - Compact donut chart
    status_counts = credit_notes_df['credit_status'].value_counts()
    
    colors = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6']
    
    fig_credit_status = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.4,
        marker=dict(colors=colors[:len(status_counts)], line=dict(color='#ffffff', width=2))
    )])
    
    fig_credit_status.update_traces(
        textposition='inside',
        textinfo='percent',
        textfont_size=11,
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig_credit_status.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(t=40, b=40, l=20, r=20),
        height=250
    )
    
    # Yearly Credit Note Trends - Compact line chart
    credit_notes_df['year'] = credit_notes_df['Date'].dt.year
    yearly_credits = credit_notes_df.groupby('year').agg({
        'Total': 'sum',
        'CreditNoteNumber': 'count'
    }).reset_index()

    fig_yearly_credits = go.Figure()
    fig_yearly_credits.add_trace(go.Scatter(
        x=yearly_credits['year'],
        y=yearly_credits['Total'],
        mode='lines+markers',
        name='Credit Amount',
        line=dict(color='#10b981', width=3),
        marker=dict(size=6, color='#10b981'),
        fill='tonexty',
        fillcolor='rgba(16, 185, 129, 0.1)',
        hovertemplate='<b>%{x}</b><br>Credit Amount: $%{y:,.0f}<extra></extra>'
    ))

    fig_yearly_credits.update_layout(
        xaxis=dict(title="Year", tickangle=0, tickfont=dict(size=10), showgrid=False),
        yaxis=dict(title="Amount ($)", tickfont=dict(size=10), tickformat='$,.0f', showgrid=False),
        hovermode='x unified',
        showlegend=False,
        margin=dict(t=40, b=60, l=60, r=20),
        height=250
    )

    return fig_credit_status, fig_yearly_credits

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="dashboard-title"> Funding Invoice Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner('Loading data...'):
        invoices_df, credit_notes_df = load_data()
    
    if invoices_df is None or credit_notes_df is None:
        st.error("Failed to load data. Please ensure the CSV files are in the correct directory.")
        return
    
    # Sidebar filters
    st.sidebar.header(" Filters")
    
    # Date range filter
    if 'invoice_date' in invoices_df.columns:
        min_date = invoices_df['invoice_date'].min()
        max_date = invoices_df['invoice_date'].max()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            invoices_df = invoices_df[
                (invoices_df['invoice_date'] >= pd.Timestamp(start_date)) &
                (invoices_df['invoice_date'] <= pd.Timestamp(end_date))
            ]
    
    # Payment status filter
    payment_statuses = invoices_df['payment_status'].unique()
    selected_statuses = st.sidebar.multiselect(
        "Payment Status",
        payment_statuses,
        default=payment_statuses
    )
    invoices_df = invoices_df[invoices_df['payment_status'].isin(selected_statuses)]
    
    # Calculate metrics
    metrics = calculate_key_metrics(invoices_df, credit_notes_df)
    
    # KPI Section - Clean 4x2 layout with better spacing
    st.header(" Key Performance Indicators")
    
    # First row of KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Total Invoices</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{metrics['total_invoices']:,}</div>
            </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Total Revenue</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{format_currency_compact(metrics['total_invoice_amount'])}</div>
            </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Amount Collected</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{format_currency_compact(metrics['total_amount_paid'])}</div>
            </div>
        ''', unsafe_allow_html=True)

    with col4:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Outstanding</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{format_currency_compact(metrics['total_outstanding'])}</div>
            </div>
        ''', unsafe_allow_html=True)

    # Second row of KPIs
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Average Invoice</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{format_currency_compact(metrics['avg_invoice_amount'])}</div>
            </div>
        ''', unsafe_allow_html=True)

    with col6:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Credit Notes</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{metrics['total_credit_notes']:,}</div>
            </div>
        ''', unsafe_allow_html=True)

    with col7:
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Credit Amount</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{format_currency_compact(metrics['total_credit_amount'])}</div>
            </div>
        ''', unsafe_allow_html=True)

    with col8:
        collection_rate = (metrics['total_amount_paid'] / metrics['total_invoice_amount'] * 100) if metrics['total_invoice_amount'] > 0 else 0
        st.markdown(f'''
            <div class="kpi-card" style="text-align:center;">
                <div style="font-size:0.9rem; color:#6b7280; font-weight:600; margin-bottom:0.5rem;">Collection Rate</div>
                <div style="font-size:1.8rem; font-weight:800; color:#1f2937;">{collection_rate:.0f}%</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Section - Clean 2x2 grid layout
    st.header(" Analytics Dashboard")
    
    # Get all charts
    fig_payment_status, fig_monthly_trends = create_overview_charts(invoices_df, credit_notes_df, metrics)
    fig_top_students, fig_amount_dist, fig_hours_amount = create_financial_analysis(invoices_df, credit_notes_df)
    fig_credit_status, fig_monthly_credits = create_credit_note_analysis(credit_notes_df)
    
    # First row of charts
    chart_row1_col1, chart_row1_col2 = st.columns(2)
    
    with chart_row1_col1:
        st.subheader("Payment Status Distribution")
        st.plotly_chart(fig_payment_status, use_container_width=True, config={'displayModeBar': False})
    
    with chart_row1_col2:
        st.subheader("Monthly Revenue Trend")
        st.plotly_chart(fig_monthly_trends, use_container_width=True, config={'displayModeBar': False})
    
    # Second row of charts
    chart_row2_col1, chart_row2_col2 = st.columns(2)
    
    with chart_row2_col1:
        st.subheader("Invoice Amount Distribution")
        st.plotly_chart(fig_amount_dist, use_container_width=True, config={'displayModeBar': False})
    
    with chart_row2_col2:
        st.subheader("Amount by Payment Status")
        st.plotly_chart(fig_hours_amount, use_container_width=True, config={'displayModeBar': False})
    
    # Third row of charts
    chart_row3_col1, chart_row3_col2 = st.columns(2)
    
    with chart_row3_col1:
        st.subheader("Credit Note Status")
        st.plotly_chart(fig_credit_status, use_container_width=True, config={'displayModeBar': False})
    
    with chart_row3_col2:
        st.subheader("Monthly Credit Trends")
        st.plotly_chart(fig_monthly_credits, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    
    # Top Students Chart - Full width
    st.header(" Top Students by Revenue")
    st.plotly_chart(fig_top_students, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    
    # Data Tables - Clean side-by-side layout
    st.header(" Recent Transactions")
    
    table_col1, table_col2 = st.columns(2)
    
    with table_col1:
        st.subheader("Recent Invoices")
        recent_invoices = invoices_df.sort_values('created', ascending=False).head(8)
        display_columns = ['invoice_number', 'display_name', 'total', 'payment_status']
        display_df = recent_invoices[display_columns].copy()
        display_df.columns = ['Invoice #', 'Student', 'Amount', 'Status']
        st.dataframe(display_df, use_container_width=True, height=300)
    
    with table_col2:
        st.subheader("Recent Credit Notes")
        recent_credits = credit_notes_df.sort_values('created', ascending=False).head(8)
        display_columns_credit = ['CreditNoteNumber', 'student_name', 'Total', 'credit_status']
        display_df_credit = recent_credits[display_columns_credit].copy()
        display_df_credit.columns = ['Credit #', 'Student', 'Amount', 'Status']
        st.dataframe(display_df_credit, use_container_width=True, height=300)


if __name__ == "__main__":
    main()