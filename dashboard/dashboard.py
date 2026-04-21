import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mysql.connector

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SCM Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp { background: #0d0f14; color: #e2e8f0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111318;
    border-right: 1px solid #1e2330;
}
section[data-testid="stSidebar"] * { color: #94a3b8 !important; }
section[data-testid="stSidebar"] .stRadio label { 
    padding: 8px 12px; border-radius: 6px; cursor: pointer;
    transition: background 0.2s;
}
section[data-testid="stSidebar"] .stRadio label:hover { background: #1e2330; }

/* Metric cards */
.kpi-card {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-good::before  { background: #10b981; }
.kpi-warn::before  { background: #f59e0b; }
.kpi-bad::before   { background: #ef4444; }
.kpi-neutral::before { background: #3b82f6; }

.kpi-label { font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin-bottom: 6px; font-family: 'IBM Plex Mono', monospace; }
.kpi-value { font-size: 32px; font-weight: 600; color: #f1f5f9; line-height: 1; font-family: 'IBM Plex Mono', monospace; }
.kpi-target { font-size: 11px; color: #475569; margin-top: 6px; }
.kpi-delta-good { color: #10b981; font-size: 12px; font-weight: 600; }
.kpi-delta-bad  { color: #ef4444; font-size: 12px; font-weight: 600; }

/* Page title */
.page-title {
    font-size: 22px; font-weight: 600; color: #f1f5f9;
    border-bottom: 1px solid #1e2330;
    padding-bottom: 12px; margin-bottom: 24px;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: -0.02em;
}
.page-sub { font-size: 13px; color: #475569; margin-top: 4px; font-family: 'IBM Plex Sans', sans-serif; }

/* Plotly charts */
.js-plotly-plot { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#111318",
    plot_bgcolor="#111318",
    font_color="#94a3b8",
    font_family="IBM Plex Sans",
)

# ── DB connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return mysql.connector.connect(
        host="localhost", port=3306,
        user="root", password="root@123",
        database="scm_db"
    )

@st.cache_data(ttl=300)
def query(sql):
    conn = get_conn()
    return pd.read_sql(sql, conn)

# ── Sidebar nav ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📦 SCM Dashboard")
    st.markdown("---")
    page = st.radio("Navigation", [
        "📊 Executive Summary",
        "🏭 Inventory Management",
        "🚚 Order Fulfilment",
        "📈 Demand Forecasting",
        "🤝 Supplier Management",
        "🤖 ML Model Performance",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small style='color:#334155'>Supply Chain Analytics<br>2024 Data</small>", unsafe_allow_html=True)

# ── Helper ────────────────────────────────────────────────────────────────────
def kpi_card(label, value, target=None, unit="", status="neutral"):
    delta_html = ""
    if target is not None:
        delta_html = f'<div class="kpi-target">Target: {target}{unit}</div>'
    st.markdown(f"""
    <div class="kpi-card kpi-{status}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}{unit}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def section(title, sub=""):
    sub_html = f'<div class="page-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="page-title">{title}{sub_html}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Executive Summary
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Executive Summary":
    section("Executive Summary", "High-level KPI scorecard · 2024")

    exec_df   = query("SELECT * FROM vw_executive_kpi_summary ORDER BY month")
    order_df  = query("SELECT * FROM vw_order_kpis ORDER BY month")
    stock_df  = query("SELECT * FROM vw_stockout_rate ORDER BY month")
    demand_df = query("SELECT * FROM vw_demand_variability")

    # Latest month values
    otif      = round(order_df["otif_pct"].mean(), 1)
    stockout  = round(stock_df["stockout_rate_pct"].mean(), 1)
    forecast  = round(demand_df["avg_forecast_accuracy_pct"].mean(), 1)
    backorder = round(order_df["backorder_rate_pct"].mean(), 1)
    cycle     = round(order_df["avg_order_cycle_time_days"].mean(), 1)
    revenue   = round(order_df["total_revenue"].sum() / 1e6, 2)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("On-Time In-Full (OTIF)", otif, 95, "%",
                 "good" if otif >= 95 else "bad")
        kpi_card("Backorder Rate", backorder, "<3", "%",
                 "good" if backorder <= 3 else "bad")
    with c2:
        kpi_card("Stockout Rate", stockout, "<5", "%",
                 "good" if stockout <= 5 else "warn")
        kpi_card("Avg Order Cycle Time", cycle, "<5", " days",
                 "good" if cycle <= 5 else "bad")
    with c3:
        kpi_card("Forecast Accuracy", forecast, ">85", "%",
                 "good" if forecast >= 85 else "warn")
        kpi_card("Total Revenue (2024)", f"{revenue}M", unit="",
                 status="neutral")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(order_df, x="month", y="total_revenue",
                      title="Revenue Trend 2024",
                      markers=True, color_discrete_sequence=["#3b82f6"])
        fig.update_layout(**PLOTLY_THEME, title_font_size=14,
                          xaxis_title="", yaxis_title="Revenue (USD)")
        fig.update_traces(line_width=2)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=order_df["month"], y=order_df["otif_pct"],
                                  name="OTIF %", line=dict(color="#10b981", width=2), mode="lines+markers"))
        fig2.add_trace(go.Scatter(x=stock_df["month"], y=stock_df["stockout_rate_pct"],
                                  name="Stockout %", line=dict(color="#ef4444", width=2), mode="lines+markers"))
        fig2.add_hline(y=95, line_dash="dash", line_color="#10b981", opacity=0.4, annotation_text="OTIF Target 95%")
        fig2.add_hline(y=5,  line_dash="dash", line_color="#ef4444", opacity=0.4, annotation_text="Stockout Limit 5%")
        fig2.update_layout(**PLOTLY_THEME, title="OTIF vs Stockout Trend",
                           title_font_size=14, xaxis_title="", yaxis_title="%")
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Inventory Management
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏭 Inventory Management":
    section("Inventory Management", "Stock levels · Holding costs · Turnover")

    inv_df  = query("SELECT * FROM vw_current_inventory")
    turn_df = query("SELECT * FROM vw_inventory_turnover ORDER BY month_key")
    hold_df = query("SELECT * FROM vw_holding_cost")

    # Filters
    f1, f2 = st.columns(2)
    with f1:
        wh = st.multiselect("Warehouse", inv_df["warehouse_city"].unique(),
                             default=list(inv_df["warehouse_city"].unique()))
    with f2:
        cats = st.multiselect("Category", inv_df["category"].unique(),
                              default=list(inv_df["category"].unique()))

    filtered = inv_df[inv_df["warehouse_city"].isin(wh) & inv_df["category"].isin(cats)]

    # KPI row
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Avg Inventory Turnover",
                 round(turn_df["inventory_turnover_ratio"].mean(), 2),
                 ">6", "x", "good" if turn_df["inventory_turnover_ratio"].mean() >= 6 else "warn")
    with k2:
        kpi_card("Avg Days of Inventory",
                 round(turn_df["days_inventory_outstanding"].mean(), 1),
                 "<60", " days",
                 "good" if turn_df["days_inventory_outstanding"].mean() <= 60 else "bad")
    with k3:
        total_hc = filtered["monthly_holding_cost"].sum()
        kpi_card("Total Holding Cost", f"${total_hc:,.0f}", status="neutral")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        bar_df = filtered.groupby("warehouse_city")["quantity_on_hand"].sum().reset_index()
        fig = px.bar(bar_df, x="warehouse_city", y="quantity_on_hand",
                     title="Stock by Warehouse", color_discrete_sequence=["#3b82f6"])
        fig.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Units")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        hc_cat = hold_df.groupby("category")["total_holding_cost"].sum().reset_index()
        fig2 = px.pie(hc_cat, names="category", values="total_holding_cost",
                      title="Holding Cost by Category", hole=0.45,
                      color_discrete_sequence=px.colors.sequential.Blues_r)
        fig2.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.line(turn_df, x="month_key", y="inventory_turnover_ratio",
                       title="Inventory Turnover Trend", markers=True,
                       color_discrete_sequence=["#a78bfa"])
        fig3.add_hline(y=6, line_dash="dash", line_color="#10b981",
                       annotation_text="Target 6x")
        fig3.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Turnover Ratio")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.line(turn_df, x="month_key", y="days_inventory_outstanding",
                       title="Days of Inventory Outstanding", markers=True,
                       color_discrete_sequence=["#f59e0b"])
        fig4.add_hline(y=60, line_dash="dash", line_color="#ef4444",
                       annotation_text="Target 60 days")
        fig4.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Days")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Current Inventory Status")

    def color_stock(val):
        if val < 20:   return "background-color:#7f1d1d;color:#fca5a5"
        elif val < 50: return "background-color:#78350f;color:#fcd34d"
        else:          return "background-color:#14532d;color:#86efac"

    display_cols = ["product_name", "warehouse_city", "category",
                    "quantity_on_hand", "reorder_level", "monthly_holding_cost"]
    show_df = filtered[display_cols].copy()
    show_df["monthly_holding_cost"] = show_df["monthly_holding_cost"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(show_df, use_container_width=True, height=300)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Order Fulfilment & Logistics
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🚚 Order Fulfilment":
    section("Order Fulfilment & Logistics", "Delivery performance · Carrier analysis")

    order_df  = query("SELECT * FROM vw_order_kpis ORDER BY month")
    trans_df  = query("SELECT * FROM vw_transportation_kpis")
    stock_df  = query("SELECT * FROM vw_stockout_rate ORDER BY month")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("OTIF %", round(order_df["otif_pct"].mean(), 1), 95, "%",
                 "good" if order_df["otif_pct"].mean() >= 95 else "bad")
    with k2:
        kpi_card("Backorder Rate", round(order_df["backorder_rate_pct"].mean(), 1), "<3", "%",
                 "good" if order_df["backorder_rate_pct"].mean() <= 3 else "bad")
    with k3:
        kpi_card("Avg Cycle Time", round(order_df["avg_order_cycle_time_days"].mean(), 1), "<5", " days",
                 "good" if order_df["avg_order_cycle_time_days"].mean() <= 5 else "bad")
    with k4:
        kpi_card("Total Freight Cost", f"${trans_df['total_freight_cost'].sum():,.0f}", status="neutral")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(order_df, x="month", y="otif_pct",
                      title="OTIF % Monthly Trend", markers=True,
                      color_discrete_sequence=["#10b981"])
        fig.add_hline(y=95, line_dash="dash", line_color="#f59e0b",
                      annotation_text="Target 95%")
        fig.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="OTIF %")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        melt_df = order_df[["month", "delivered", "cancelled", "backordered"]].melt(
            id_vars="month", var_name="status", value_name="count")
        fig2 = px.bar(melt_df, x="month", y="count", color="status",
                      title="Order Status Breakdown",
                      color_discrete_map={"delivered": "#10b981",
                                          "cancelled": "#ef4444",
                                          "backordered": "#f59e0b"})
        fig2.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Orders")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        carrier_cost = trans_df.groupby("carrier")["total_freight_cost"].sum().reset_index()
        fig3 = px.bar(carrier_cost, x="carrier", y="total_freight_cost",
                      title="Freight Cost by Carrier",
                      color_discrete_sequence=["#3b82f6"])
        fig3.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Cost (USD)")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        carrier_delay = trans_df.groupby("carrier")["delay_rate_pct"].mean().reset_index()
        fig4 = px.bar(carrier_delay, x="carrier", y="delay_rate_pct",
                      title="Delay Rate by Carrier",
                      color_discrete_sequence=["#ef4444"])
        fig4.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Delay Rate %")
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Demand Forecasting
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Demand Forecasting":
    section("Demand Forecasting", "Accuracy · Variability · ML predictions")

    demand_df = query("SELECT * FROM vw_demand_kpis ORDER BY month")
    var_df    = query("SELECT * FROM vw_demand_variability")

    try:
        forecast_df = pd.read_csv("demand_forecast.csv")
    except:
        forecast_df = None

    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Avg Forecast Accuracy", round(var_df["avg_forecast_accuracy_pct"].mean(), 1),
                 ">85", "%", "good" if var_df["avg_forecast_accuracy_pct"].mean() >= 85 else "warn")
    with k2:
        kpi_card("Avg Demand Variability CV", round(var_df["demand_variability_cv_pct"].mean(), 1),
                 "<20", "%", "good" if var_df["demand_variability_cv_pct"].mean() <= 20 else "warn")
    with k3:
        kpi_card("Avg Forecast Error", round(var_df["avg_forecast_error_pct"].mean(), 1),
                 unit="%", status="neutral")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=demand_df["month"], y=demand_df["actual_demand"],
                                 name="Actual", line=dict(color="#3b82f6", width=2), mode="lines+markers"))
        fig.add_trace(go.Scatter(x=demand_df["month"], y=demand_df["forecasted_demand"],
                                 name="Forecast", line=dict(color="#f59e0b", width=2, dash="dash"), mode="lines+markers"))
        fig.update_layout(**PLOTLY_THEME, title="Actual vs Forecast Demand",
                          title_font_size=14, xaxis_title="", yaxis_title="Units")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.line(demand_df, x="month", y="forecast_accuracy_pct",
                       title="Forecast Accuracy % by Month", markers=True,
                       color_discrete_sequence=["#10b981"])
        fig2.add_hline(y=85, line_dash="dash", line_color="#f59e0b",
                       annotation_text="Target 85%")
        fig2.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Accuracy %")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        prod_err = var_df.groupby("product_name")["avg_forecast_error_pct"].mean().reset_index().sort_values(
            "avg_forecast_error_pct", ascending=False).head(10)
        fig3 = px.bar(prod_err, x="avg_forecast_error_pct", y="product_name",
                      orientation="h", title="Top 10 Forecast Error by Product",
                      color_discrete_sequence=["#ef4444"])
        fig3.update_layout(**PLOTLY_THEME, xaxis_title="Error %", yaxis_title="")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        cat_var = var_df.groupby("category")["demand_variability_cv_pct"].mean().reset_index()
        fig4 = px.bar(cat_var, x="category", y="demand_variability_cv_pct",
                      title="Demand Variability by Category",
                      color_discrete_sequence=["#a78bfa"])
        fig4.add_hline(y=20, line_dash="dash", line_color="#f59e0b",
                       annotation_text="Target <20%")
        fig4.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="CV %")
        st.plotly_chart(fig4, use_container_width=True)

    if forecast_df is not None:
        st.markdown("#### ML Predicted Demand (Next Quarter)")
        fig5 = px.line(forecast_df, x="month", y="predicted_demand",
                       color="product_id" if "product_id" in forecast_df.columns else None,
                       title="Predicted Demand Jan–Mar 2025",
                       color_discrete_sequence=px.colors.qualitative.Set2)
        fig5.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Predicted Units")
        st.plotly_chart(fig5, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Supplier Management
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤝 Supplier Management":
    section("Supplier Management", "Fill rate · Lead time · Spend analysis")

    sup_df = query("SELECT * FROM vw_supplier_performance")

    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Avg Fill Rate", round(sup_df["fill_rate_pct"].mean(), 1), ">95", "%",
                 "good" if sup_df["fill_rate_pct"].mean() >= 95 else "warn")
    with k2:
        kpi_card("Avg Delay Days", round(sup_df["avg_delay_days"].mean(), 1), "0", " days",
                 "good" if sup_df["avg_delay_days"].mean() == 0 else "bad")
    with k3:
        kpi_card("Total Spend", f"${sup_df['total_spend'].sum():,.0f}", status="neutral")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(sup_df.sort_values("total_spend", ascending=False),
                     x="supplier_name", y="total_spend",
                     title="Spend by Supplier", color_discrete_sequence=["#3b82f6"])
        fig.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Spend (USD)",
                          xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sup_scatter = sup_df.copy()
        sup_scatter["total_spend"] = sup_scatter["total_spend"].fillna(0)
        sup_scatter["reliability_score"] = sup_scatter["reliability_score"].fillna(0)
        sup_scatter["fill_rate_pct"] = sup_scatter["fill_rate_pct"].fillna(0)
        fig2 = px.scatter(sup_scatter, x="reliability_score", y="fill_rate_pct",
                          size="total_spend", color="supplier_category",
                          hover_name="supplier_name",
                          title="Reliability vs Fill Rate (bubble = spend)",
                          size_max=40,
                          color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(**PLOTLY_THEME, xaxis_title="Reliability Score",
                           yaxis_title="Fill Rate %")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.bar(sup_df.sort_values("avg_delay_days", ascending=False),
                      x="supplier_name", y="avg_delay_days",
                      title="Avg Delay Days by Supplier",
                      color_discrete_sequence=["#ef4444"])
        fig3.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Days",
                           xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        cat_spend = sup_df.groupby("supplier_category")["total_spend"].sum().reset_index()
        fig4 = px.pie(cat_spend, names="supplier_category", values="total_spend",
                      title="Spend by Category", hole=0.45,
                      color_discrete_sequence=px.colors.sequential.Purples_r)
        fig4.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Supplier Performance Scorecard")

    def highlight_fill(val):
        if val < 90:  return "background-color:#7f1d1d;color:#fca5a5"
        elif val < 95: return "background-color:#78350f;color:#fcd34d"
        else:          return "background-color:#14532d;color:#86efac"

    def highlight_delay(val):
        if val > 3: return "background-color:#7f1d1d;color:#fca5a5"
        elif val > 0: return "background-color:#78350f;color:#fcd34d"
        else:         return "background-color:#14532d;color:#86efac"

    scorecard_cols = ["supplier_name", "fill_rate_pct", "avg_delay_days",
                      "on_time_po_rate_pct", "total_spend", "reliability_score"]
    available_cols = [c for c in scorecard_cols if c in sup_df.columns]
    st.dataframe(
        sup_df[available_cols].style
            .map(highlight_fill, subset=["fill_rate_pct"])
            .map(highlight_delay, subset=["avg_delay_days"]),
        use_container_width=True,
        height=300
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — ML Model Performance
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 ML Model Performance":
    section("ML Model Performance", "Model accuracy · Predictions · Anomalies")

    try:
        import json
        with open("model_metrics.json") as f:
            metrics = json.load(f)
        has_metrics = True
    except:
        has_metrics = False
        metrics = {}

    try:
        stockout_pred = pd.read_csv("stockout_predictions.csv")
    except:
        stockout_pred = None

    try:
        delay_pred = pd.read_csv("delay_predictions.csv")
    except:
        delay_pred = None

    try:
        anomaly_df = pd.read_csv("anomaly_inventory.csv")
    except:
        anomaly_df = None

    try:
        forecast_df = pd.read_csv("demand_forecast.csv")
    except:
        forecast_df = None

    # Metric cards
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        val = round(metrics.get("demand_forecast", {}).get("r2", 0), 3) if has_metrics else "N/A"
        kpi_card("Demand Forecast R²", val, status="neutral")
    with k2:
        val = round(metrics.get("demand_forecast", {}).get("mae", 0), 1) if has_metrics else "N/A"
        kpi_card("Forecast MAE", val, status="neutral")
    with k3:
        val = f"{round(metrics.get('stockout_classifier', {}).get('accuracy', 0)*100, 1)}%" if has_metrics else "N/A"
        kpi_card("Stockout Accuracy", val, status="neutral")
    with k4:
        val = f"{round(metrics.get('delay_predictor', {}).get('accuracy', 0)*100, 1)}%" if has_metrics else "N/A"
        kpi_card("Delay Accuracy", val, status="neutral")
    with k5:
        if anomaly_df is not None and "anomaly_label" in anomaly_df.columns:
            rate = round((anomaly_df["anomaly_label"] == "Anomaly").mean() * 100, 1)
            kpi_card("Anomaly Rate", rate, unit="%", status="warn")
        else:
            kpi_card("Anomaly Rate", "N/A", status="neutral")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if stockout_pred is not None and "risk_label" in stockout_pred.columns:
            dist = stockout_pred["risk_label"].value_counts().reset_index()
            dist.columns = ["label", "count"]
            fig = px.bar(dist, x="label", y="count",
                         title="Stockout Risk Distribution",
                         color="label",
                         color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"})
            fig.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Count", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("stockout_predictions.csv not found or missing risk_label column")

    with col2:
        if delay_pred is not None and "delay_label" in delay_pred.columns:
            dist2 = delay_pred["delay_label"].value_counts().reset_index()
            dist2.columns = ["label", "count"]
            fig2 = px.bar(dist2, x="label", y="count",
                          title="Delay Prediction Distribution",
                          color="label",
                          color_discrete_map={"Delayed": "#ef4444", "On Time": "#10b981"})
            fig2.update_layout(**PLOTLY_THEME, xaxis_title="", yaxis_title="Count", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("delay_predictions.csv not found or missing delay_label column")

    if anomaly_df is not None and "anomaly_score" in anomaly_df.columns and "quantity_on_hand" in anomaly_df.columns:
        st.markdown("#### Anomaly Score Distribution")
        fig3 = px.scatter(anomaly_df, x="anomaly_score", y="quantity_on_hand",
                          color="anomaly_label" if "anomaly_label" in anomaly_df.columns else None,
                          title="Anomaly Score vs Quantity on Hand",
                          color_discrete_map={"Anomaly": "#ef4444", "Normal": "#3b82f6"})
        fig3.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig3, use_container_width=True)

    if forecast_df is not None:
        st.markdown("#### Next Quarter Demand Forecast Table")
        st.dataframe(forecast_df.head(50), use_container_width=True, height=300)