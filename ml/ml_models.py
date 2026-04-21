"""
ml_models.py
────────────
Four ML models for the SCM dashboard (aligned with requirements):
  1. Demand Forecasting        – Random Forest Regressor (primary) + Linear Regression
  2. Stockout Risk Classifier  – Logistic Regression
  3. Delivery Delay Predictor  – Decision Tree Classifier
  4. Inventory Anomaly Detection – Isolation Forest (NEW — requirement: anomaly detection)

Outputs:
  demand_forecast.csv
  stockout_predictions.csv
  delay_predictions.csv
  anomaly_inventory.csv      ← NEW
  model_metrics.json

KPIs powered by these models (per requirements doc):
  - Demand Variability / Forecast Accuracy → Model 1
  - Stockout Rate                          → Model 2
  - On-Time Delivery / Delay Rate          → Model 3
  - Inventory anomalies                    → Model 4

Prerequisites:
  pip install pandas scikit-learn matplotlib joblib mysql-connector-python

Usage:
  python ml_models.py
"""

import os
import json
import pandas as pd
import numpy as np
import mysql.connector
from sklearn.linear_model    import LinearRegression, LogisticRegression
from sklearn.ensemble        import RandomForestRegressor, IsolationForest
from sklearn.tree            import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, classification_report
)
import joblib

# ── CONFIG ─────────────────────────────────────────────────────────────────
MYSQL_CONFIG = {
    "host": "localhost", "port": 3306,
    "user": "root", "password": "root@123",
    "database": "scm_db"
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = BASE_DIR                                      # outputs beside this script
MODEL_DIR = os.path.join(BASE_DIR, "saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)
# ───────────────────────────────────────────────────────────────────────────


def db_query(sql: str) -> pd.DataFrame:
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    df   = pd.read_sql(sql, conn)
    conn.close()
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  MODEL 1 – DEMAND FORECASTING
#  Uses demand_history.
#  Predicts next 3 months demand per product.
#  KPIs: Forecast Accuracy %, Demand Variability
# ══════════════════════════════════════════════════════════════════════════════
def train_demand_forecast():
    print("\n[1/4] Demand Forecasting …")

    df = db_query("""
        SELECT dh.product_id, p.category, dh.year, dh.month,
               dh.actual_demand, dh.forecasted_demand, dh.forecast_error_pct
        FROM demand_history dh
        JOIN products p ON dh.product_id = p.product_id
        ORDER BY dh.product_id, dh.year, dh.month
    """)

    le_cat = LabelEncoder()
    le_prd = LabelEncoder()
    df["category_enc"] = le_cat.fit_transform(df["category"])
    df["product_enc"]  = le_prd.fit_transform(df["product_id"])

    # Lag features for time-series style regression
    df = df.sort_values(["product_id", "year", "month"]).reset_index(drop=True)
    df["lag1"] = df.groupby("product_id")["actual_demand"].shift(1)
    df["lag2"] = df.groupby("product_id")["actual_demand"].shift(2)
    df["lag3"] = df.groupby("product_id")["actual_demand"].shift(3)
    df.dropna(inplace=True)

    features = ["month", "product_enc", "category_enc", "lag1", "lag2", "lag3"]
    X = df[features]
    y = df["actual_demand"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Linear Regression baseline
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)

    # Random Forest — better captures seasonal non-linearity
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    metrics = {
        "LinearRegression": {
            "MAE":  round(float(mean_absolute_error(y_test, lr_pred)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_test, lr_pred))), 2),
            "R2":   round(float(r2_score(y_test, lr_pred)), 4)
        },
        "RandomForest": {
            "MAE":  round(float(mean_absolute_error(y_test, rf_pred)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_test, rf_pred))), 2),
            "R2":   round(float(r2_score(y_test, rf_pred)), 4)
        }
    }
    print(f"   LR   MAE={metrics['LinearRegression']['MAE']}   R²={metrics['LinearRegression']['R2']}")
    print(f"   RF   MAE={metrics['RandomForest']['MAE']}    R²={metrics['RandomForest']['R2']}")

    joblib.dump(rf,     os.path.join(MODEL_DIR, "demand_rf.pkl"))
    joblib.dump(le_prd, os.path.join(MODEL_DIR, "label_encoder_product.pkl"))
    joblib.dump(le_cat, os.path.join(MODEL_DIR, "label_encoder_category.pkl"))

    # Predict next 3 months (Jan–Mar 2025) using the Random Forest
    forecast_rows = []
    for pid in df["product_id"].unique():
        sub  = df[df["product_id"] == pid].sort_values("month")
        if len(sub) < 3:
            continue
        l1   = float(sub.iloc[-1]["actual_demand"])
        l2   = float(sub.iloc[-2]["actual_demand"])
        l3   = float(sub.iloc[-3]["actual_demand"])
        penc = int(sub.iloc[-1]["product_enc"])
        cenc = int(sub.iloc[-1]["category_enc"])

        for future_month in [1, 2, 3]:
            X_new = pd.DataFrame(
                [[future_month, penc, cenc, l1, l2, l3]], columns=features
            )
            pred = float(rf.predict(X_new)[0])
            forecast_rows.append({
                "product_id":       pid,
                "year":             2025,
                "month":            future_month,
                "predicted_demand": int(max(0, pred))
            })
            l3, l2, l1 = l2, l1, pred

    forecast_df = pd.DataFrame(forecast_rows)
    forecast_df.to_csv(os.path.join(DATA_DIR, "demand_forecast.csv"), index=False)
    print(f"   ✓ demand_forecast.csv saved ({len(forecast_df)} rows)")

    return metrics


# ══════════════════════════════════════════════════════════════════════════════
#  MODEL 2 – STOCKOUT RISK CLASSIFIER
#  Uses inventory. Labels HIGH / LOW stockout risk.
#  KPI: Stockout Rate
# ══════════════════════════════════════════════════════════════════════════════
def train_stockout_classifier():
    print("\n[2/4] Stockout Risk Classification …")

    df = db_query("""
        SELECT i.product_id, i.warehouse_id,
               i.quantity_on_hand, i.quantity_reserved,
               i.quantity_in_transit, i.reorder_triggered,
               p.reorder_level, p.max_stock_level, p.shelf_life_days
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
    """)

    # Label: 1 = high stockout risk if stock < 1.5x reorder_level
    df["stockout_risk"]   = (df["quantity_on_hand"] < 1.5 * df["reorder_level"]).astype(int)
    df["stock_ratio"]     = df["quantity_on_hand"] / df["max_stock_level"].replace(0, np.nan)
    df["available_stock"] = df["quantity_on_hand"] - df["quantity_reserved"]

    le_p = LabelEncoder()
    le_w = LabelEncoder()
    df["product_enc"]   = le_p.fit_transform(df["product_id"])
    df["warehouse_enc"] = le_w.fit_transform(df["warehouse_id"])

    features = [
        "quantity_on_hand", "quantity_reserved", "quantity_in_transit",
        "reorder_level", "max_stock_level", "shelf_life_days",
        "stock_ratio", "available_stock", "product_enc", "warehouse_enc"
    ]
    df_clean = df[features + ["stockout_risk"]].dropna()
    X = df_clean[features]
    y = df_clean["stockout_risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    print(f"   Accuracy: {acc}")
    print(classification_report(y_test, y_pred, target_names=["Low Risk", "High Risk"]))

    joblib.dump(clf, os.path.join(MODEL_DIR, "stockout_clf.pkl"))

    df_clean = df_clean.copy()
    df_clean["predicted_risk"] = clf.predict(X)
    df_clean["risk_label"]     = df_clean["predicted_risk"].map({0: "Low Risk", 1: "High Risk"})

    # Merge product/warehouse IDs back
    out = df[["product_id", "warehouse_id", "quantity_on_hand",
              "reorder_level", "stock_ratio"]].copy()
    out = out.loc[df_clean.index]
    out["risk_label"] = df_clean["risk_label"].values
    out.to_csv(os.path.join(DATA_DIR, "stockout_predictions.csv"), index=False)
    print(f"   ✓ stockout_predictions.csv saved ({len(out)} rows)")

    return {"accuracy": acc}


# ══════════════════════════════════════════════════════════════════════════════
#  MODEL 3 – DELIVERY DELAY PREDICTOR
#  Uses logistics + orders. Predicts is_delayed (0/1).
#  KPI: On-Time Delivery Rate, Delay Rate
# ══════════════════════════════════════════════════════════════════════════════
def train_delay_predictor():
    print("\n[3/4] Delivery Delay Prediction …")

    df = db_query("""
        SELECT l.carrier, l.distance_km, l.transit_hours,
               l.freight_cost, l.is_delayed,
               o.discount_pct, o.payment_method, o.delivery_city
        FROM logistics l
        JOIN orders o ON l.order_id = o.order_id
        WHERE l.is_delayed IS NOT NULL
    """)
    df.dropna(inplace=True)

    le_c = LabelEncoder()
    le_p = LabelEncoder()
    le_d = LabelEncoder()
    df["carrier_enc"] = le_c.fit_transform(df["carrier"])
    df["payment_enc"] = le_p.fit_transform(df["payment_method"])
    df["city_enc"]    = le_d.fit_transform(df["delivery_city"])

    features = [
        "distance_km", "transit_hours", "freight_cost",
        "discount_pct", "carrier_enc", "payment_enc", "city_enc"
    ]
    X = df[features]
    y = df["is_delayed"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    dt = DecisionTreeClassifier(max_depth=5, random_state=42, class_weight="balanced")
    dt.fit(X_train, y_train)
    y_pred = dt.predict(X_test)

    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    print(f"   Accuracy: {acc}")
    print(classification_report(y_test, y_pred, target_names=["On Time", "Delayed"]))

    joblib.dump(dt, os.path.join(MODEL_DIR, "delay_dt.pkl"))

    df["predicted_delay"] = dt.predict(X)
    df["delay_label"]     = df["predicted_delay"].map({0: "On Time", 1: "Delayed"})
    out = df[["carrier", "distance_km", "transit_hours",
              "freight_cost", "is_delayed", "delay_label"]].copy()
    out.to_csv(os.path.join(DATA_DIR, "delay_predictions.csv"), index=False)
    print(f"   ✓ delay_predictions.csv saved ({len(out)} rows)")

    return {"accuracy": acc}


# ══════════════════════════════════════════════════════════════════════════════
#  MODEL 4 – INVENTORY ANOMALY DETECTION  (NEW — per requirements)
#  Uses inventory snapshots. Flags unusual stock levels using Isolation Forest.
#  Power BI use: anomaly overlay on inventory trend charts
# ══════════════════════════════════════════════════════════════════════════════
def train_anomaly_detector():
    print("\n[4/4] Inventory Anomaly Detection (Isolation Forest) …")

    df = db_query("""
        SELECT i.inventory_id, i.product_id, i.warehouse_id,
               i.snapshot_date, i.quantity_on_hand,
               i.quantity_reserved, i.quantity_in_transit,
               i.reorder_triggered, p.reorder_level, p.max_stock_level,
               p.unit_cost
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
    """)

    le_p = LabelEncoder()
    le_w = LabelEncoder()
    df["product_enc"]   = le_p.fit_transform(df["product_id"])
    df["warehouse_enc"] = le_w.fit_transform(df["warehouse_id"])
    df["stock_ratio"]   = df["quantity_on_hand"] / df["max_stock_level"].replace(0, np.nan)
    df["holding_value"] = df["quantity_on_hand"] * df["unit_cost"]

    features = [
        "quantity_on_hand", "quantity_reserved", "quantity_in_transit",
        "stock_ratio", "holding_value", "product_enc", "warehouse_enc"
    ]
    df_clean = df[features + ["inventory_id", "product_id", "warehouse_id",
                               "snapshot_date"]].dropna()

    X = df_clean[features]

    # contamination=0.05 → flags top 5% outlier inventory records
    iso = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso.fit(X)
    df_clean = df_clean.copy()
    df_clean["anomaly_score"]  = iso.decision_function(X)
    df_clean["is_anomaly"]     = (iso.predict(X) == -1).astype(int)
    df_clean["anomaly_label"]  = df_clean["is_anomaly"].map(
        {0: "Normal", 1: "Anomaly"}
    )

    n_anomalies = int(df_clean["is_anomaly"].sum())
    print(f"   Anomalies detected: {n_anomalies} / {len(df_clean)} records "
          f"({round(n_anomalies/len(df_clean)*100, 1)}%)")

    joblib.dump(iso, os.path.join(MODEL_DIR, "anomaly_iso.pkl"))

    out = df_clean[[
        "inventory_id", "product_id", "warehouse_id", "snapshot_date",
        "quantity_on_hand", "stock_ratio", "anomaly_score",
        "is_anomaly", "anomaly_label"
    ]].copy()
    out["anomaly_score"] = out["anomaly_score"].round(4)
    out.to_csv(os.path.join(DATA_DIR, "anomaly_inventory.csv"), index=False)
    print(f"   ✓ anomaly_inventory.csv saved ({len(out)} rows)")

    return {
        "total_records": len(df_clean),
        "anomalies_detected": n_anomalies,
        "anomaly_rate_pct": round(n_anomalies / len(df_clean) * 100, 2)
    }


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    all_metrics = {}
    all_metrics["demand_forecast"]    = train_demand_forecast()
    all_metrics["stockout_risk"]      = train_stockout_classifier()
    all_metrics["delay_predictor"]    = train_delay_predictor()
    all_metrics["anomaly_detection"]  = train_anomaly_detector()

    metrics_path = os.path.join(DATA_DIR, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n✅ All 4 models trained. Metrics saved to model_metrics.json")
    print("\nGenerated CSVs for Streamlit import:")
    print("  demand_forecast.csv      → Demand Forecasting page")
    print("  stockout_predictions.csv → Inventory Risk page")
    print("  delay_predictions.csv    → Logistics page")
    print("  anomaly_inventory.csv    → Anomaly Detection overlay")
    print("  model_metrics.json       → ML Performance card")
