# Power BI Dashboard – Supply Chain Management
## Setup Guide & KPI Implementation

---

## Prerequisites

1. **MySQL Connector for Power BI**
   Download: https://dev.mysql.com/downloads/connector/net/
   Install the MySQL Connector/NET (required for Power BI to connect to MySQL)

2. **Power BI Desktop** (free) — https://powerbi.microsoft.com/desktop

3. **Database ready** — schema.sql run + data loaded via load_to_mysql.py

---

## Step 1 — Connect Power BI to MySQL

1. Open Power BI Desktop → **Get Data** → Search "MySQL" → Select **MySQL Database**
2. Enter:
   - Server: `localhost`
   - Database: `scm_db`
3. Click **OK** → Select **Import** mode (recommended for dashboards)
4. In the Navigator, select ALL of these views:

   | View Name                   | Powers                                  |
   |-----------------------------|-----------------------------------------|
   | vw_current_inventory        | Inventory KPIs, Stockout cards          |
   | vw_inventory_turnover       | Inventory Turnover Ratio, DIO           |
   | vw_order_kpis               | OTIF%, Cycle Time, Backorder Rate       |
   | vw_stockout_rate            | Stockout Rate % trend                   |
   | vw_demand_kpis              | Forecast Accuracy per product/month     |
   | vw_demand_variability       | Demand Variability CV%                  |
   | vw_transportation_kpis      | Freight Cost, Delay Rate                |
   | vw_supplier_performance     | Supplier Fill Rate, Lead Time           |
   | vw_holding_cost             | Holding Cost by warehouse & category    |
   | vw_executive_kpi_summary    | Executive scorecard (all KPIs monthly)  |

5. Also import these **ML output CSVs** via **Get Data → Text/CSV**:
   - `demand_forecast.csv`
   - `stockout_predictions.csv`
   - `delay_predictions.csv`
   - `anomaly_inventory.csv`

6. Click **Load**

---

## Step 2 — Set Up Relationships (Model View)

In Power BI → **Model View**, verify/create these relationships:

```
vw_current_inventory.product_id  →  vw_inventory_turnover.product_id
vw_order_kpis.month              →  vw_stockout_rate.month
vw_order_kpis.month              →  vw_executive_kpi_summary.month
vw_demand_kpis.product_id        →  vw_demand_variability.product_id
vw_transportation_kpis.month     →  vw_order_kpis.month
demand_forecast.product_id       →  vw_demand_kpis.product_id
stockout_predictions.product_id  →  vw_current_inventory.product_id
```

---

## Step 3 — Create DAX Measures

In the **Data** pane, right-click any table → **New Measure**

### Inventory KPIs

```dax
-- Inventory Turnover Ratio (average across all products)
Avg Inventory Turnover =
AVERAGE(vw_inventory_turnover[inventory_turnover_ratio])

-- Days of Inventory Outstanding
Avg DIO =
AVERAGE(vw_inventory_turnover[days_inventory_outstanding])

-- Total Holding Cost (current month)
Total Holding Cost =
SUM(vw_holding_cost[total_holding_cost])

-- Stockout Rate %
Stockout Rate % =
AVERAGE(vw_stockout_rate[stockout_rate_pct])
```

### Order & Fulfilment KPIs

```dax
-- OTIF % (On-Time In-Full)
OTIF % =
AVERAGE(vw_order_kpis[otif_pct])

-- Backorder Rate %
Backorder Rate % =
AVERAGE(vw_order_kpis[backorder_rate_pct])

-- Average Order Cycle Time (days)
Avg Order Cycle Time =
AVERAGE(vw_order_kpis[avg_order_cycle_time_days])

-- Total Revenue
Total Revenue =
SUM(vw_order_kpis[total_revenue])
```

### Demand KPIs

```dax
-- Forecast Accuracy %
Avg Forecast Accuracy % =
AVERAGE(vw_demand_variability[avg_forecast_accuracy_pct])

-- Demand Variability (Coefficient of Variation %)
Avg Demand Variability CV =
AVERAGE(vw_demand_variability[demand_variability_cv_pct])
```

### Cost KPIs

```dax
-- Total Transportation Cost
Total Transportation Cost =
SUM(vw_transportation_kpis[total_freight_cost])

-- Avg Cost per KM
Avg Cost per KM =
AVERAGE(vw_transportation_kpis[cost_per_km])
```

---

## Step 4 — Dashboard Pages

Build 6 pages in Power BI. Use **Insert → Text Box** for page titles.

---

### PAGE 1 — Executive Summary

**Purpose:** Single-screen KPI scorecard for management

**Visuals to add:**

| Visual Type  | Fields                                     | Title                        |
|--------------|--------------------------------------------|------------------------------|
| KPI Card     | OTIF %  (target: 95%)                      | On-Time Delivery Rate        |
| KPI Card     | Stockout Rate %  (target: <5%)             | Stockout Rate                |
| KPI Card     | Avg Forecast Accuracy % (target: >85%)     | Forecast Accuracy            |
| KPI Card     | Backorder Rate % (target: <3%)             | Backorder Rate               |
| KPI Card     | Avg Order Cycle Time (target: <5 days)     | Order Cycle Time (days)      |
| KPI Card     | Total Revenue                              | Monthly Revenue              |
| Line Chart   | month → total_revenue (vw_order_kpis)      | Revenue Trend (2024)         |
| Line Chart   | month → otif_pct, stockout_rate_pct        | OTIF vs Stockout Trend       |
| Slicer       | month (vw_executive_kpi_summary)           | Month Filter                 |

**How to add a KPI Card:**
1. Click the KPI visual icon in the Visualizations pane
2. Drag measure to **Value**, set target in **Target Value**
3. In Format → Callout Value → set color: green if above target, red if below

---

### PAGE 2 — Inventory Management

**Purpose:** Stock health, reorder alerts, holding cost

**Visuals to add:**

| Visual Type     | Fields                                               | Title                         |
|-----------------|------------------------------------------------------|-------------------------------|
| Table           | product_name, warehouse_city, quantity_on_hand,      | Current Inventory Status      |
|                 | reorder_level, stock_pct, monthly_holding_cost       |                               |
| Bar Chart       | warehouse_city → SUM(quantity_on_hand)               | Stock by Warehouse            |
| Stacked Bar     | category → SUM(quantity_on_hand) by warehouse_city   | Stock by Category & Warehouse |
| Line Chart      | month → Avg Inventory Turnover                       | Inventory Turnover Trend      |
| Line Chart      | month → Avg DIO                                      | Days of Inventory Outstanding |
| Card            | SUM(monthly_holding_cost) from vw_current_inventory  | Total Holding Cost            |
| Donut Chart     | category → SUM(monthly_holding_cost)                 | Holding Cost by Category      |
| Conditional     | reorder_triggered = 1 rows highlighted red           | ← Apply via conditional format|
| Table (ML)      | product_id, warehouse_id, risk_label (stockout_pred) | ML Stockout Risk Alerts       |

**Conditional Formatting on Inventory Table:**
- Select the table → Format → Conditional Formatting → stock_pct
- Rules: < 20% = Red, 20–50% = Yellow, > 50% = Green

**Anomaly Overlay:**
1. Add a scatter chart: snapshot_date (X) vs quantity_on_hand (Y)
2. Color legend: anomaly_label from anomaly_inventory.csv
3. Red dots = anomalies, Blue = Normal

**Slicers:** warehouse_city, category, snapshot_date (range)

---

### PAGE 3 — Order Fulfilment & Logistics

**Purpose:** Order performance, delivery efficiency, carrier comparison

**Visuals to add:**

| Visual Type      | Fields                                               | Title                          |
|------------------|------------------------------------------------------|--------------------------------|
| Line Chart       | month → otif_pct                                     | OTIF % Monthly Trend           |
| Bar Chart        | month → delivered, cancelled, backordered            | Order Status Breakdown         |
| KPI Card         | Avg Order Cycle Time                                 | Avg Order Cycle Time (days)    |
| KPI Card         | Backorder Rate %                                     | Backorder Rate                 |
| Bar Chart        | carrier → total_freight_cost (transportation_kpis)   | Freight Cost by Carrier        |
| Bar Chart        | carrier → delay_rate_pct                             | Delay Rate by Carrier          |
| Map Visual       | destination_city (logistics) → freight_cost          | Freight Cost Heat Map          |
| Table (ML)       | carrier, distance_km, delay_label (delay_pred csv)   | ML Delay Predictions           |
| Scatter          | distance_km (X) → freight_cost (Y), colored carrier  | Distance vs Cost by Carrier    |

**Map setup:**
1. Add a **Map** or **Filled Map** visual
2. Location: destination_city
3. Size: SUM(freight_cost)
4. Tooltip: total_shipments, avg_transit_hours

**Slicers:** carrier, origin_warehouse_id, month, shipment_status

---

### PAGE 4 — Demand Forecasting

**Purpose:** Historical demand, forecast accuracy, ML predictions

**Visuals to add:**

| Visual Type   | Fields                                                | Title                          |
|---------------|-------------------------------------------------------|--------------------------------|
| Line Chart    | month → actual_demand & forecasted_demand             | Actual vs Forecast (2024)      |
| Line Chart    | month → forecast_accuracy_pct (vw_demand_kpis)        | Forecast Accuracy % by Month   |
| Bar Chart     | product_name → avg_forecast_error_pct                 | Forecast Error by Product      |
| Line Chart    | month (from demand_forecast.csv) → predicted_demand   | Predicted Demand Jan–Mar 2025  |
| Bar Chart     | category → demand_variability_cv_pct                  | Demand Variability by Category |
| Table         | product_name, avg_monthly_demand, demand_std_dev,     | Demand Variability Summary     |
|               | demand_variability_cv_pct, avg_forecast_accuracy_pct  |                                |

**Combining actuals with forecast:**
1. In the Line Chart, add two lines:
   - Line 1: month → actual_demand (from vw_demand_kpis) — solid line
   - Line 2: month → predicted_demand (from demand_forecast.csv) — dashed line
2. Use a legend color to distinguish historical vs predicted

**Slicers:** product_name, category, year

---

### PAGE 5 — Procurement & Supplier Management

**Purpose:** Supplier KPIs, lead time analysis, procurement efficiency

**Visuals to add:**

| Visual Type   | Fields                                               | Title                          |
|---------------|------------------------------------------------------|--------------------------------|
| Table         | supplier_name, fill_rate_pct, avg_delay_days,        | Supplier Performance Scorecard |
|               | on_time_po_rate_pct, total_spend, reliability_score  |                                |
| Bar Chart     | supplier_name → total_spend                          | Spend by Supplier              |
| Bar Chart     | supplier_name → avg_delay_days                       | Avg Delay Days by Supplier     |
| Scatter       | reliability_score (X) → fill_rate_pct (Y)            | Reliability vs Fill Rate       |
|               | Bubble size: total_spend                             |                                |
| KPI Card      | AVG(fill_rate_pct)                                   | Avg Supplier Fill Rate         |
| KPI Card      | AVG(avg_delay_days)                                  | Avg Procurement Delay (days)   |
| Donut Chart   | supplier_category → total_spend                      | Spend by Category              |

**Conditional Formatting on Scorecard Table:**
- fill_rate_pct: Red if < 90%, Yellow 90–95%, Green > 95%
- avg_delay_days: Red if > 3 days, Green if = 0

**Slicers:** supplier_category, country

---

### PAGE 6 — ML Model Performance

**Purpose:** Show ML model accuracy for transparency and project documentation

**Visuals to add:**

| Visual Type     | Fields / Source                                    | Title                           |
|-----------------|----------------------------------------------------|---------------------------------|
| Card            | RF R² from model_metrics.json                      | Demand Forecast R²              |
| Card            | RF MAE from model_metrics.json                     | Demand Forecast MAE             |
| Card            | Stockout Classifier Accuracy                       | Stockout Classifier Accuracy    |
| Card            | Delay Predictor Accuracy                           | Delay Predictor Accuracy        |
| Card            | anomaly_rate_pct                                   | Anomaly Detection Rate          |
| Bar Chart       | risk_label → COUNT (stockout_predictions)          | Stockout Risk Distribution      |
| Bar Chart       | delay_label → COUNT (delay_predictions)            | Delay Prediction Distribution   |
| Table           | product_id, predicted_demand (demand_forecast)     | Next Quarter Demand Forecast    |
| Scatter         | anomaly_score vs quantity_on_hand, colored anomaly | Anomaly Score Distribution      |

**Loading model_metrics.json:**
1. Get Data → JSON → select model_metrics.json
2. Expand the nested records to get individual metric columns
3. Use Card visuals for each metric value

---

## Step 5 — Interactivity & Filters

### Cross-Page Filters
1. Go to **View → Sync Slicers**
2. Add a **Month slicer** and sync it across: Pages 1, 2, 3, 4
3. Add a **Category slicer** and sync across Pages 2, 4

### Drill-Through
1. On Page 2 (Inventory), right-click a product row → Drill Through to Page 4 (Demand)
2. Set up: Page 4 → Drill Through → Add product_name as drill-through field

### Tooltips
- On all charts, add relevant metrics to the Tooltip field well for on-hover detail

### Bookmarks (for Presentation)
1. View → Bookmarks → Add Bookmark for each page state
2. Use these bookmarks during the 10-minute class presentation

---

## Step 6 — Formatting & Theming

1. **View → Themes → Browse for themes** — use a clean corporate theme
2. Recommended color scheme:
   - Green (#2ECC71) for good/on-target metrics
   - Red (#E74C3C) for at-risk / below-target
   - Blue (#3498DB) for neutral / trend charts
   - Orange (#F39C12) for warning / medium risk
3. Add your company logo: **Insert → Image**
4. Use **Text Boxes** for page subtitles explaining each KPI

---

## KPI Reference — All 10 Required Metrics

| # | KPI                        | Source View                | Target        | Visual         |
|---|----------------------------|----------------------------|---------------|----------------|
| 1 | Inventory Turnover Ratio   | vw_inventory_turnover      | > 6x/year     | KPI Card + Line|
| 2 | Stockout Rate %            | vw_stockout_rate           | < 5%          | KPI Card + Line|
| 3 | Days of Inventory (DIO)    | vw_inventory_turnover      | < 60 days     | KPI Card       |
| 4 | Order Cycle Time           | vw_order_kpis              | < 5 days      | KPI Card       |
| 5 | OTIF % (On-Time Delivery)  | vw_order_kpis              | > 95%         | KPI Card + Line|
| 6 | Backorder Rate %           | vw_order_kpis              | < 3%          | KPI Card       |
| 7 | Forecast Accuracy %        | vw_demand_variability      | > 85%         | KPI Card + Bar |
| 8 | Demand Variability (CV%)   | vw_demand_variability      | < 20%         | Bar Chart      |
| 9 | Holding Cost               | vw_holding_cost            | Monitor trend | Card + Donut   |
|10 | Transportation Cost        | vw_transportation_kpis     | Monitor trend | Bar + Line     |

---

## Saving & Publishing

1. Save the file as `SCM_Dashboard.pbix`
2. For team sharing: **File → Publish → Publish to Power BI** (requires free account)
3. For submission: Export each page as PDF via **File → Export → Export to PDF**
4. File naming: `SCM22CS_P1_[SRN1]-[SRN2]-[SRN3].pdf`
