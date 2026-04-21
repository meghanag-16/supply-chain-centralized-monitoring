"""
load_to_mysql.py
────────────────
Loads all generated CSVs into MySQL (scm_db).

Compatible with updated schema:
  - products table now has holding_cost_rate column
  - orders table supports 'Backordered' status
  - All NaN → NULL handling for Power BI compatibility

Prerequisites:
  pip install pandas mysql-connector-python

Usage:
  1. Run schema.sql first to create the database and tables
  2. Run generate_dataset.py to produce the CSV files
  3. Run this script: python load_to_mysql.py
"""

import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# ── CONFIG ─────────────────────────────────────────────────────────────────
MYSQL_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "ammu@1510",   # ← change to your MySQL password
    "database": "scm_db"
}

DATA_DIR = Path(__file__).parent.parent / "data"
# ───────────────────────────────────────────────────────────────────────────


def get_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Could not connect to MySQL: {e}")
        raise


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all NaN / NaT / empty strings to Python None (SQL NULL safe).
    Ensures Power BI reads nullable columns correctly.
    """
def clean_dataframe(df):
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)
    df = df.replace("", None)
    return df


def load_table(conn, csv_file: str, table: str, chunk_size: int = 500):
    path = os.path.join(DATA_DIR, csv_file)
    if not os.path.exists(path):
        print(f"  ⚠  Skipped {table} — file not found: {path}")
        return

    df = pd.read_csv(path, keep_default_na=True)
    df = clean_dataframe(df)

    cols         = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    col_str      = ", ".join([f"`{c}`" for c in cols])
    sql          = f"INSERT IGNORE INTO `{table}` ({col_str}) VALUES ({placeholders})"

    cursor = conn.cursor()

    # Safe row conversion — handle any remaining NaN/inf at the value level
    rows = []
    for r in df.itertuples(index=False, name=None):
        row = []
        for v in r:
            if v is None:
                row.append(None)
            elif isinstance(v, float) and (pd.isna(v) or v != v):
                row.append(None)
            else:
                row.append(v)
        rows.append(tuple(row))

    # Chunked insert
    for i in range(0, len(rows), chunk_size):
        cursor.executemany(sql, rows[i: i + chunk_size])

    conn.commit()
    cursor.close()
    print(f"  ✓ {table:<25}  {len(rows):>5} rows loaded")


def run():
    print("Connecting to MySQL …")
    conn = get_connection()
    print(f"Connected to '{MYSQL_CONFIG['database']}' on {MYSQL_CONFIG['host']}.\n")

    # Load order matters — respect FK dependencies
    tables = [
        ("suppliers.csv",      "suppliers"),
        ("products.csv",       "products"),       # has holding_cost_rate
        ("warehouses.csv",     "warehouses"),
        ("inventory.csv",      "inventory"),
        ("orders.csv",         "orders"),          # has 'Backordered' status
        ("order_items.csv",    "order_items"),
        ("procurement.csv",    "procurement"),
        ("logistics.csv",      "logistics"),
        ("demand_history.csv", "demand_history"),
    ]

    success_count = 0
    for csv_file, table in tables:
        try:
            load_table(conn, csv_file, table)
            success_count += 1
        except Exception as e:
            print(f"\n  ❌ Error loading {table}: {e}")
            continue

    conn.close()
    print(f"\n✅ Done. {success_count}/{len(tables)} tables loaded successfully.")
    print("\nPower BI setup:")
    print("  1. Open Power BI Desktop")
    print("  2. Get Data → MySQL Database")
    print("  3. Server: localhost:3306  |  Database: scm_db")
    print("  4. Import these views: vw_current_inventory, vw_inventory_turnover,")
    print("     vw_order_kpis, vw_stockout_rate, vw_demand_kpis,")
    print("     vw_demand_variability, vw_transportation_kpis,")
    print("     vw_supplier_performance, vw_holding_cost, vw_executive_kpi_summary")


if __name__ == "__main__":
    run()
