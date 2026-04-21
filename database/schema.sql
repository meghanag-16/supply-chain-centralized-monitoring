-- ============================================================
-- Supply Chain Management – MySQL Schema
-- Database: scm_db
-- Aligned with: Centralized SCM Monitoring Requirements
-- Covers: Inventory, Demand, Orders, Procurement, Logistics
-- Run this file FIRST before loading any data
-- ============================================================

CREATE DATABASE IF NOT EXISTS scm_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE scm_db;

-- ─────────────────────────────────────────────
-- 1. SUPPLIERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id          VARCHAR(10)   PRIMARY KEY,
    supplier_name        VARCHAR(100)  NOT NULL,
    category             VARCHAR(50),
    country              VARCHAR(50),
    city                 VARCHAR(50),
    lead_time_days       INT,
    reliability_score    DECIMAL(4,2),
    contract_start_date  DATE,
    is_active            TINYINT(1)    DEFAULT 1
);

-- ─────────────────────────────────────────────
-- 2. PRODUCTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id        VARCHAR(10)   PRIMARY KEY,
    product_name      VARCHAR(150)  NOT NULL,
    category          VARCHAR(60),
    unit_price        DECIMAL(10,2),
    unit_cost         DECIMAL(10,2),
    supplier_id       VARCHAR(10),
    reorder_level     INT,
    max_stock_level   INT,
    shelf_life_days   INT,
    weight_kg         DECIMAL(8,3),
    -- NEW: monthly holding cost rate (% of unit_cost per month, e.g. 0.02 = 2%)
    holding_cost_rate DECIMAL(5,4)  DEFAULT 0.0200,
    CONSTRAINT fk_product_supplier
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- 3. WAREHOUSES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id    VARCHAR(6)    PRIMARY KEY,
    warehouse_name  VARCHAR(100)  NOT NULL,
    city            VARCHAR(50),
    state           VARCHAR(50),
    capacity_units  INT,
    manager_name    VARCHAR(80),
    is_active       TINYINT(1)    DEFAULT 1
);

-- ─────────────────────────────────────────────
-- 4. INVENTORY
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id         INT           AUTO_INCREMENT PRIMARY KEY,
    product_id           VARCHAR(10)   NOT NULL,
    warehouse_id         VARCHAR(6)    NOT NULL,
    snapshot_date        DATE          NOT NULL,
    quantity_on_hand     INT           DEFAULT 0,
    quantity_reserved    INT           DEFAULT 0,
    quantity_in_transit  INT           DEFAULT 0,
    reorder_triggered    TINYINT(1)    DEFAULT 0,
    last_updated         DATETIME,
    CONSTRAINT fk_inv_product
        FOREIGN KEY (product_id)   REFERENCES products(product_id),
    CONSTRAINT fk_inv_warehouse
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ─────────────────────────────────────────────
-- 5. ORDERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id        VARCHAR(12)   PRIMARY KEY,
    customer_id     VARCHAR(12),
    order_date      DATE,
    ship_date       DATE,
    delivery_date   DATE,
    status          VARCHAR(20),
    -- NEW: 'Backordered' added as a valid status for backorder rate KPI
    warehouse_id    VARCHAR(6),
    total_amount    DECIMAL(12,2),
    discount_pct    INT           DEFAULT 0,
    payment_method  VARCHAR(30),
    delivery_city   VARCHAR(50),
    is_on_time      TINYINT(1),
    CONSTRAINT fk_order_warehouse
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ─────────────────────────────────────────────
-- 6. ORDER_ITEMS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  INT           AUTO_INCREMENT PRIMARY KEY,
    order_id       VARCHAR(12)   NOT NULL,
    product_id     VARCHAR(10)   NOT NULL,
    quantity       INT,
    unit_price     DECIMAL(10,2),
    line_total     DECIMAL(12,2),
    CONSTRAINT fk_oi_order
        FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    CONSTRAINT fk_oi_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ─────────────────────────────────────────────
-- 7. PROCUREMENT
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS procurement (
    po_id                   VARCHAR(12)   PRIMARY KEY,
    supplier_id             VARCHAR(10),
    product_id              VARCHAR(10),
    warehouse_id            VARCHAR(6),
    po_date                 DATE,
    expected_delivery_date  DATE,
    actual_delivery_date    DATE,
    quantity_ordered        INT,
    quantity_received       INT,
    unit_cost               DECIMAL(10,2),
    total_cost              DECIMAL(12,2),
    status                  VARCHAR(20),
    delay_days              INT           DEFAULT 0,
    CONSTRAINT fk_po_supplier
        FOREIGN KEY (supplier_id)  REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_po_product
        FOREIGN KEY (product_id)   REFERENCES products(product_id),
    CONSTRAINT fk_po_warehouse
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ─────────────────────────────────────────────
-- 8. LOGISTICS / SHIPMENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS logistics (
    shipment_id              VARCHAR(12)   PRIMARY KEY,
    order_id                 VARCHAR(12),
    carrier                  VARCHAR(50),
    origin_warehouse_id      VARCHAR(6),
    destination_city         VARCHAR(50),
    dispatch_date            DATE,
    estimated_delivery_date  DATE,
    actual_delivery_date     DATE,
    distance_km              INT,
    transit_hours            DECIMAL(6,1),
    freight_cost             DECIMAL(10,2),
    shipment_status          VARCHAR(20),
    is_delayed               TINYINT(1)    DEFAULT 0,
    CONSTRAINT fk_log_order
        FOREIGN KEY (order_id)            REFERENCES orders(order_id),
    CONSTRAINT fk_log_warehouse
        FOREIGN KEY (origin_warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ─────────────────────────────────────────────
-- 9. DEMAND_HISTORY
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS demand_history (
    demand_id           INT           AUTO_INCREMENT PRIMARY KEY,
    product_id          VARCHAR(10),
    year                INT,
    month               INT,
    actual_demand       INT,
    forecasted_demand   INT,
    forecast_error_pct  DECIMAL(6,2),
    CONSTRAINT fk_dh_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
);


-- ============================================================
-- VIEWS  – KPI-Aligned for Power BI Direct Query / Import
-- Covers ALL 10 KPIs from the requirement document:
--   1. Inventory Turnover Ratio
--   2. Stockout Rate
--   3. Days of Inventory Outstanding (DIO)
--   4. Order Cycle Time
--   5. On-Time Delivery Rate (OTIF %)
--   6. Backorder Rate
--   7. Forecast Accuracy %
--   8. Demand Variability
--   9. Holding Cost
--  10. Transportation Cost
-- ============================================================


-- ─────────────────────────────────────────────
-- VIEW 1: Current Inventory Status (latest snapshot)
-- Powers: Stockout Rate, Inventory Turnover, DIO, Holding Cost
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_current_inventory AS
SELECT
    i.product_id,
    p.product_name,
    p.category,
    i.warehouse_id,
    w.city                                                    AS warehouse_city,
    w.warehouse_name,
    i.quantity_on_hand,
    i.quantity_reserved,
    i.quantity_in_transit,
    i.reorder_triggered,
    p.reorder_level,
    p.max_stock_level,
    p.unit_cost,
    p.holding_cost_rate,
    -- Holding cost = qty_on_hand × unit_cost × monthly holding rate
    ROUND(i.quantity_on_hand * p.unit_cost * p.holding_cost_rate, 2)
                                                              AS monthly_holding_cost,
    ROUND((i.quantity_on_hand / NULLIF(p.max_stock_level, 0)) * 100, 1)
                                                              AS stock_pct,
    i.snapshot_date
FROM inventory i
JOIN products   p ON i.product_id   = p.product_id
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
WHERE i.snapshot_date = (
    SELECT MAX(snapshot_date) FROM inventory
);


-- ─────────────────────────────────────────────
-- VIEW 2: Monthly Inventory Turnover & DIO
-- Formula:
--   Turnover = Units Sold / Avg Inventory
--   DIO      = (Avg Inventory / Units Sold) × Days_in_Month
-- FIX: Changed GROUP BY to use full expression instead of alias
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_inventory_turnover AS
SELECT
    oi_monthly.month_key,
    oi_monthly.product_id,
    p.product_name,
    p.category,
    oi_monthly.units_sold,
    inv_avg.avg_inventory,
    ROUND(
        oi_monthly.units_sold / NULLIF(inv_avg.avg_inventory, 0), 2
    ) AS inventory_turnover_ratio,
    ROUND(
        (inv_avg.avg_inventory / NULLIF(oi_monthly.units_sold, 0)) * 30, 1
    ) AS days_inventory_outstanding
FROM (
    SELECT
        DATE_FORMAT(o.order_date, '%Y-%m') AS month_key,
        oi.product_id,
        SUM(oi.quantity) AS units_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.status = 'Delivered'
    GROUP BY DATE_FORMAT(o.order_date, '%Y-%m'), oi.product_id
) oi_monthly
JOIN (
    SELECT
        DATE_FORMAT(snapshot_date, '%Y-%m') AS month_key,
        product_id,
        AVG(quantity_on_hand) AS avg_inventory
    FROM inventory
    GROUP BY DATE_FORMAT(snapshot_date, '%Y-%m'), product_id
) inv_avg
ON oi_monthly.month_key = inv_avg.month_key
AND oi_monthly.product_id = inv_avg.product_id
JOIN products p
ON oi_monthly.product_id = p.product_id;


-- ─────────────────────────────────────────────
-- VIEW 3: Order Fulfilment KPIs (monthly)
-- Powers: OTIF %, Order Cycle Time, Backorder Rate
-- FIX: Changed GROUP BY to use full expression instead of alias
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_order_kpis AS
SELECT
    DATE_FORMAT(order_date, '%Y-%m')                               AS month,
    COUNT(*)                                                       AS total_orders,
    SUM(total_amount)                                              AS total_revenue,
    SUM(CASE WHEN status = 'Delivered'   THEN 1 ELSE 0 END)       AS delivered,
    SUM(CASE WHEN status = 'Cancelled'   THEN 1 ELSE 0 END)       AS cancelled,
    SUM(CASE WHEN status = 'Backordered' THEN 1 ELSE 0 END)       AS backordered,
    SUM(CASE WHEN is_on_time = 1         THEN 1 ELSE 0 END)       AS on_time_deliveries,
    ROUND(AVG(total_amount), 2)                                    AS avg_order_value,

    -- OTIF % = On-Time deliveries / Total Delivered × 100
    ROUND(
        SUM(CASE WHEN is_on_time = 1 THEN 1 ELSE 0 END) /
        NULLIF(SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END), 0) * 100,
    1)                                                             AS otif_pct,

    -- Backorder Rate % = Backordered / Total Orders × 100
    ROUND(
        SUM(CASE WHEN status = 'Backordered' THEN 1 ELSE 0 END) /
        NULLIF(COUNT(*), 0) * 100,
    2)                                                             AS backorder_rate_pct,

    -- Order Cycle Time = avg days from order_date to delivery_date (delivered orders)
    ROUND(
        AVG(
            CASE WHEN status = 'Delivered' AND delivery_date IS NOT NULL
                 THEN DATEDIFF(delivery_date, order_date)
            END
        ),
    1)                                                             AS avg_order_cycle_time_days,

    -- Average Ship Lead Time = order_date to ship_date
    ROUND(
        AVG(
            CASE WHEN ship_date IS NOT NULL
                 THEN DATEDIFF(ship_date, order_date)
            END
        ),
    1)                                                             AS avg_ship_lead_time_days

FROM orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;


-- ─────────────────────────────────────────────
-- VIEW 4: Stockout Rate (monthly)
-- Stockout Rate % = Products that triggered reorder / Total products tracked × 100
-- FIX: Changed GROUP BY to use full expression instead of alias
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_stockout_rate AS
SELECT
    DATE_FORMAT(snapshot_date, '%Y-%m')          AS month,
    COUNT(*)                                     AS total_product_warehouse_combos,
    SUM(reorder_triggered)                       AS stockout_events,
    ROUND(
        SUM(reorder_triggered) /
        NULLIF(COUNT(*), 0) * 100,
    2)                                           AS stockout_rate_pct
FROM inventory
GROUP BY DATE_FORMAT(snapshot_date, '%Y-%m')
ORDER BY month;


-- ─────────────────────────────────────────────
-- VIEW 5: Demand Forecast Accuracy & Variability (monthly per product)
-- Forecast Accuracy % = 100 - avg(forecast_error_pct)
-- Demand Variability  = STDDEV(actual_demand) per product over months
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_demand_kpis AS
SELECT
    dh.product_id,
    p.product_name,
    p.category,
    dh.year,
    dh.month,
    dh.actual_demand,
    dh.forecasted_demand,
    dh.forecast_error_pct,
    ROUND(100 - dh.forecast_error_pct, 2)        AS forecast_accuracy_pct
FROM demand_history dh
JOIN products p ON dh.product_id = p.product_id;


-- ─────────────────────────────────────────────
-- VIEW 6: Demand Variability (per product — annual)
-- Demand Variability = std dev of monthly demand / avg monthly demand (CV)
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_demand_variability AS
SELECT
    dh.product_id,
    p.product_name,
    p.category,
    dh.year,
    ROUND(AVG(dh.actual_demand), 0)              AS avg_monthly_demand,
    ROUND(STDDEV(dh.actual_demand), 0)           AS demand_std_dev,
    ROUND(
        STDDEV(dh.actual_demand) /
        NULLIF(AVG(dh.actual_demand), 0) * 100,
    2)                                           AS demand_variability_cv_pct,
    ROUND(AVG(dh.forecast_error_pct), 2)         AS avg_forecast_error_pct,
    ROUND(100 - AVG(dh.forecast_error_pct), 2)  AS avg_forecast_accuracy_pct
FROM demand_history dh
JOIN products p ON dh.product_id = p.product_id
GROUP BY dh.product_id, p.product_name, p.category, dh.year;


-- ─────────────────────────────────────────────
-- VIEW 7: Transportation Cost KPIs (monthly by carrier & warehouse)
-- Powers: Transportation Cost KPI
-- FIX: Changed GROUP BY to use full expression instead of alias
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_transportation_kpis AS
SELECT
    DATE_FORMAT(l.dispatch_date, '%Y-%m')        AS month,
    l.carrier,
    w.city                                       AS origin_city,
    l.origin_warehouse_id,
    COUNT(l.shipment_id)                         AS total_shipments,
    SUM(l.freight_cost)                          AS total_freight_cost,
    ROUND(AVG(l.freight_cost), 2)                AS avg_freight_cost,
    ROUND(AVG(l.distance_km), 0)                 AS avg_distance_km,
    ROUND(AVG(l.transit_hours), 1)               AS avg_transit_hours,
    SUM(l.is_delayed)                            AS delayed_shipments,
    ROUND(
        SUM(l.is_delayed) / NULLIF(COUNT(*), 0) * 100,
    2)                                           AS delay_rate_pct,
    -- Cost per km efficiency metric
    ROUND(SUM(l.freight_cost) / NULLIF(SUM(l.distance_km), 0), 4)
                                                 AS cost_per_km
FROM logistics l
JOIN warehouses w ON l.origin_warehouse_id = w.warehouse_id
GROUP BY DATE_FORMAT(l.dispatch_date, '%Y-%m'), l.carrier, w.city, l.origin_warehouse_id
ORDER BY month, total_freight_cost DESC;


-- ─────────────────────────────────────────────
-- VIEW 8: Supplier Performance
-- Powers: Procurement KPIs (lead time, fill rate, delays)
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_supplier_performance AS
SELECT
    s.supplier_id,
    s.supplier_name,
    s.category                                                    AS supplier_category,
    s.country,
    s.reliability_score,
    s.lead_time_days                                              AS contracted_lead_time,
    COUNT(po.po_id)                                               AS total_pos,
    SUM(po.total_cost)                                            AS total_spend,
    ROUND(AVG(po.delay_days), 2)                                  AS avg_delay_days,
    -- Fill Rate % = qty received / qty ordered × 100
    ROUND(
        SUM(po.quantity_received) /
        NULLIF(SUM(po.quantity_ordered), 0) * 100,
    2)                                                            AS fill_rate_pct,
    -- On-Time PO Rate % = POs with delay_days = 0 / total POs
    ROUND(
        SUM(CASE WHEN po.delay_days = 0 THEN 1 ELSE 0 END) /
        NULLIF(COUNT(po.po_id), 0) * 100,
    2)                                                            AS on_time_po_rate_pct,
    SUM(CASE WHEN po.status = 'Partial' THEN 1 ELSE 0 END)       AS partial_deliveries
FROM suppliers s
LEFT JOIN procurement po ON s.supplier_id = po.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.category,
         s.country, s.reliability_score, s.lead_time_days;


-- ─────────────────────────────────────────────
-- VIEW 9: Holding Cost Summary (monthly per warehouse)
-- Powers: Holding Cost KPI
-- FIX: Changed GROUP BY to use full expression instead of alias
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_holding_cost AS
SELECT
    DATE_FORMAT(i.snapshot_date, '%Y-%m')        AS month,
    i.warehouse_id,
    w.city                                       AS warehouse_city,
    p.category,
    SUM(i.quantity_on_hand)                      AS total_units_held,
    -- Holding cost = qty × unit_cost × monthly holding rate
    ROUND(
        SUM(i.quantity_on_hand * p.unit_cost * p.holding_cost_rate),
    2)                                           AS total_holding_cost,
    ROUND(AVG(i.quantity_on_hand), 0)            AS avg_qty_on_hand
FROM inventory i
JOIN products   p ON i.product_id   = p.product_id
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
GROUP BY DATE_FORMAT(i.snapshot_date, '%Y-%m'), i.warehouse_id, w.city, p.category
ORDER BY month, total_holding_cost DESC;


-- ─────────────────────────────────────────────
-- VIEW 10: Executive Summary KPI Card (single-row per month)
-- Designed for Power BI KPI cards / scorecards
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_executive_kpi_summary AS
SELECT
    ok.month,
    ok.total_orders,
    ok.total_revenue,
    ok.delivered,
    ok.cancelled,
    ok.backordered,
    ok.otif_pct,
    ok.backorder_rate_pct,
    ok.avg_order_cycle_time_days,
    ok.avg_ship_lead_time_days,
    sr.stockout_rate_pct,
    ROUND(
        (SELECT SUM(freight_cost) FROM logistics
         WHERE DATE_FORMAT(dispatch_date,'%Y-%m') = ok.month),
    2)                                           AS total_freight_cost,
    ROUND(
        (SELECT SUM(i2.quantity_on_hand * p2.unit_cost * p2.holding_cost_rate)
         FROM inventory i2
         JOIN products p2 ON i2.product_id = p2.product_id
         WHERE DATE_FORMAT(i2.snapshot_date,'%Y-%m') = ok.month),
    2)                                           AS total_holding_cost
FROM vw_order_kpis ok
LEFT JOIN vw_stockout_rate sr ON ok.month = sr.month;