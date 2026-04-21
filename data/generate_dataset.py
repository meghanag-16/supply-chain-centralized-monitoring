"""
Supply Chain Dataset Generator
────────────────────────────────
Modeled after real-world SCM data from companies like Walmart, Amazon, and P&G.
Dataset covers: Suppliers, Products, Warehouses, Inventory, Orders, Logistics

Aligned with Requirements:
  - Inventory Turnover Ratio, Stockout Rate, DIO, Order Cycle Time
  - OTIF %, Backorder Rate, Forecast Accuracy, Demand Variability
  - Holding Cost, Transportation Cost

Changes from v1:
  - products: added holding_cost_rate column
  - orders: 'Backordered' added as a valid status (powers Backorder Rate KPI)
  - All outputs are Power BI-compatible CSVs (no mixed types, proper NULLs)

Run this ONCE to generate all CSV files used by the loader script.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────
# 1. SUPPLIERS  (25 rows)
# ─────────────────────────────────────────────
supplier_names = [
    "Reliance Industries", "Tata Chemicals", "Marico Ltd", "ITC Limited",
    "Hindustan Unilever", "Dabur India", "Godrej Consumer", "Emami Ltd",
    "Patanjali Ayurved", "Reckitt Benckiser", "Colgate-Palmolive", "Nestle India",
    "Parle Products", "Britannia Industries", "Amul Dairy", "Mother Dairy",
    "Balaji Wafers", "Haldiram Snacks", "MTR Foods", "Bikano Group",
    "Bonn Group", "Cremica Foods", "Priya Pickles", "Eastern Condiments",
    "ADF Foods"
]

supplier_categories = [
    "Raw Materials", "Packaging", "Electronics", "FMCG", "Dairy",
    "Snacks & Beverages", "Condiments", "Processed Foods"
]

suppliers = pd.DataFrame({
    "supplier_id": [f"SUP{str(i).zfill(3)}" for i in range(1, 26)],
    "supplier_name": supplier_names,
    "category": [random.choice(supplier_categories) for _ in range(25)],
    "country": random.choices(
        ["India", "India", "India", "China", "USA", "Germany"],
        weights=[50, 50, 50, 20, 10, 5], k=25
    ),
    "city": random.choices(
        ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad",
         "Ahmedabad", "Pune", "Kolkata", "Jaipur", "Surat"],
        k=25
    ),
    "lead_time_days": np.random.randint(3, 21, 25),
    "reliability_score": np.round(np.random.uniform(0.70, 0.99, 25), 2),
    "contract_start_date": [
        (datetime(2020, 1, 1) + timedelta(days=int(d))).strftime("%Y-%m-%d")
        for d in np.random.randint(0, 365 * 3, 25)
    ],
    "is_active": random.choices([1, 0], weights=[90, 10], k=25)
})
suppliers.to_csv(f"{OUTPUT_DIR}/suppliers.csv", index=False)
print(f"✓ suppliers.csv  — {len(suppliers)} rows")


# ─────────────────────────────────────────────
# 2. PRODUCTS  (50 rows)
# NEW: holding_cost_rate column added (2% monthly is industry standard for FMCG)
# ─────────────────────────────────────────────
product_names = [
    "Surf Excel Detergent 1kg", "Dove Soap Bar 100g", "Lux Body Wash 250ml",
    "Colgate Toothpaste 200g", "Dettol Handwash 500ml", "Pantene Shampoo 400ml",
    "Maggi Noodles 70g", "Nescafe Classic 200g", "KitKat Chocolate 40g",
    "Parle-G Biscuit 800g", "Britannia Marie 300g", "Haldiram Bhujia 400g",
    "Amul Butter 500g", "Mother Dairy Ghee 1L", "Amul Gold Milk 1L",
    "Tropicana Orange 1L", "Minute Maid Pulpy 1L", "Real Juice Mango 1L",
    "Pepsi 600ml Bottle", "Coca-Cola 750ml Bottle", "Sprite 600ml Bottle",
    "Red Bull Energy 250ml", "Paper Boat Aam Panna 250ml", "B Natural Mixed Fruit 1L",
    "Marico Saffola Oil 2L", "Fortune Sunflower Oil 5L", "Dhara Refined Oil 1L",
    "MDH Rajwadi Masala 100g", "Everest Pav Bhaji Masala 50g", "Catch Pepper 100g",
    "MTR Ready-to-Eat Palak Paneer", "MTR Ready-to-Eat Dal Makhani", "Priya Mango Pickle 500g",
    "Keya Italian Herbs", "Tata Salt 1kg", "Saffola Honey 250g",
    "Himalaya Face Wash 150ml", "Pears Soap 125g", "Vaseline Lotion 200ml",
    "Nivea Cream 200ml", "Fair & Lovely Cream 50g", "Pond's Talcum 400g",
    "Vim Dishwash Bar 200g", "Harpic Toilet Cleaner 1L", "Lizol Floor Cleaner 1L",
    "Odonil Air Freshener 75g", "Good Knight Fast Card", "HIT Mosquito Spray 200ml",
    "Mortein Coil 12pcs", "Baygon Spray 400ml"
]

# Holding cost rates vary by category:
# Dairy (perishable) = 3-4%, FMCG = 1.5-2.5%, Home Care = 1-2%
category_list = random.choices(
    ["Personal Care", "Food & Beverages", "Dairy", "Snacks",
     "Home Care", "Oils & Condiments", "Ready-to-Eat"],
    k=50
)
holding_rates = []
for cat in category_list:
    if cat == "Dairy":
        holding_rates.append(round(random.uniform(0.030, 0.040), 4))
    elif cat in ["Food & Beverages", "Ready-to-Eat", "Snacks"]:
        holding_rates.append(round(random.uniform(0.020, 0.030), 4))
    else:
        holding_rates.append(round(random.uniform(0.015, 0.025), 4))

products = pd.DataFrame({
    "product_id": [f"PRD{str(i).zfill(3)}" for i in range(1, 51)],
    "product_name": product_names,
    "category": category_list,
    "unit_price": np.round(np.random.uniform(15, 850, 50), 2),
    "unit_cost": np.round(np.random.uniform(8, 600, 50), 2),
    "supplier_id": random.choices(
        [f"SUP{str(i).zfill(3)}" for i in range(1, 26)], k=50
    ),
    "reorder_level": np.random.randint(50, 300, 50),
    "max_stock_level": np.random.randint(500, 3000, 50),
    "shelf_life_days": np.random.randint(30, 730, 50),
    "weight_kg": np.round(np.random.uniform(0.05, 5.0, 50), 3),
    # NEW: monthly holding cost rate (% of unit_cost)
    "holding_cost_rate": holding_rates,
})
products.to_csv(f"{OUTPUT_DIR}/products.csv", index=False)
print(f"✓ products.csv   — {len(products)} rows")


# ─────────────────────────────────────────────
# 3. WAREHOUSES  (8 rows)
# ─────────────────────────────────────────────
warehouses = pd.DataFrame({
    "warehouse_id": [f"WH{str(i).zfill(2)}" for i in range(1, 9)],
    "warehouse_name": [
        "Mumbai Central DC", "Delhi NCR Hub", "Bengaluru South DC",
        "Chennai Port DC", "Hyderabad Regional", "Kolkata East Hub",
        "Ahmedabad West DC", "Pune Satellite WH"
    ],
    "city": ["Mumbai", "Delhi", "Bengaluru", "Chennai",
              "Hyderabad", "Kolkata", "Ahmedabad", "Pune"],
    "state": ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu",
               "Telangana", "West Bengal", "Gujarat", "Maharashtra"],
    "capacity_units": [50000, 45000, 38000, 32000, 28000, 25000, 22000, 18000],
    "manager_name": [
        "Rajesh Sharma", "Priya Nair", "Amit Verma", "Sunita Rao",
        "Vikram Singh", "Ananya Das", "Rohit Mehta", "Kavita Joshi"
    ],
    "is_active": [1] * 8
})
warehouses.to_csv(f"{OUTPUT_DIR}/warehouses.csv", index=False)
print(f"✓ warehouses.csv — {len(warehouses)} rows")


# ─────────────────────────────────────────────
# 4. INVENTORY  (Weekly snapshots)
# ─────────────────────────────────────────────
inventory_rows = []
snapshot_dates = pd.date_range("2024-01-01", "2024-12-31", freq="W")

for date in snapshot_dates:
    for wh_id in warehouses["warehouse_id"]:
        sample_prds = random.sample(list(products["product_id"]), 6)
        for prd_id in sample_prds:
            prod = products[products["product_id"] == prd_id].iloc[0]
            qty = int(np.random.normal(
                loc=(prod["reorder_level"] + prod["max_stock_level"]) / 2,
                scale=(prod["max_stock_level"] - prod["reorder_level"]) / 4
            ))
            qty = max(0, min(qty, prod["max_stock_level"]))
            inventory_rows.append({
                "inventory_id": None,
                "product_id": prd_id,
                "warehouse_id": wh_id,
                "snapshot_date": date.strftime("%Y-%m-%d"),
                "quantity_on_hand": qty,
                "quantity_reserved": int(qty * random.uniform(0.05, 0.25)),
                "quantity_in_transit": int(np.random.randint(0, 200)),
                "reorder_triggered": 1 if qty < prod["reorder_level"] else 0,
                "last_updated": date.strftime("%Y-%m-%d %H:%M:%S")
            })

inventory = pd.DataFrame(inventory_rows)
inventory["inventory_id"] = range(1, len(inventory) + 1)
inventory.to_csv(f"{OUTPUT_DIR}/inventory.csv", index=False)
print(f"✓ inventory.csv  — {len(inventory)} rows")


# ─────────────────────────────────────────────
# 5. ORDERS  (500 customer orders)
# NEW: 'Backordered' status added (~4% of orders) for Backorder Rate KPI
# ─────────────────────────────────────────────
customers = [f"CUST{str(i).zfill(4)}" for i in range(1, 201)]

# Updated: Backordered status added
order_statuses = ["Placed", "Confirmed", "Shipped", "In Transit",
                  "Delivered", "Cancelled", "Backordered"]
status_weights  = [5, 8, 10, 10, 57, 5, 5]

orders_list = []
for i in range(1, 501):
    order_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
    status = random.choices(order_statuses, weights=status_weights)[0]

    ship_date = None
    del_date  = None

    if status not in ("Placed", "Backordered"):
        ship_date = order_date + timedelta(days=random.randint(1, 3))
    if status == "Delivered" and ship_date:
        del_date = ship_date + timedelta(days=random.randint(2, 7))

    is_on_time = None
    if del_date and ship_date:
        is_on_time = 1 if (del_date - ship_date).days <= 5 else 0

    orders_list.append({
        "order_id":       f"ORD{str(i).zfill(5)}",
        "customer_id":    random.choice(customers),
        "order_date":     order_date.strftime("%Y-%m-%d"),
        "ship_date":      ship_date.strftime("%Y-%m-%d") if ship_date else "",
        "delivery_date":  del_date.strftime("%Y-%m-%d") if del_date else "",
        "status":         status,
        "warehouse_id":   random.choice(list(warehouses["warehouse_id"])),
        "total_amount":   round(random.uniform(150, 12000), 2),
        "discount_pct":   random.choice([0, 5, 10, 15, 20]),
        "payment_method": random.choice(["UPI", "Credit Card", "COD", "Net Banking"]),
        "delivery_city":  random.choice([
            "Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad",
            "Kolkata", "Ahmedabad", "Pune", "Jaipur", "Lucknow"
        ]),
        "is_on_time": is_on_time if is_on_time is not None else ""
    })

orders = pd.DataFrame(orders_list)
orders.to_csv(f"{OUTPUT_DIR}/orders.csv", index=False)
print(f"✓ orders.csv     — {len(orders)} rows")


# ─────────────────────────────────────────────
# 6. ORDER_ITEMS  (1–4 items per order)
# ─────────────────────────────────────────────
order_items_list = []
oi_id = 1
for _, order in orders.iterrows():
    n_items = random.randint(1, 4)
    selected_products = random.sample(list(products["product_id"]), n_items)
    for prd_id in selected_products:
        prod = products[products["product_id"] == prd_id].iloc[0]
        qty = random.randint(1, 20)
        order_items_list.append({
            "order_item_id": oi_id,
            "order_id":      order["order_id"],
            "product_id":    prd_id,
            "quantity":      qty,
            "unit_price":    prod["unit_price"],
            "line_total":    round(qty * prod["unit_price"], 2)
        })
        oi_id += 1

order_items = pd.DataFrame(order_items_list)
order_items.to_csv(f"{OUTPUT_DIR}/order_items.csv", index=False)
print(f"✓ order_items.csv— {len(order_items)} rows")


# ─────────────────────────────────────────────
# 7. PROCUREMENT  (200 purchase orders)
# ─────────────────────────────────────────────
proc_list = []
for i in range(1, 201):
    prd = products.sample(1).iloc[0]
    sup = suppliers[suppliers["supplier_id"] == prd["supplier_id"]].iloc[0]
    po_date       = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
    expected_days = int(sup["lead_time_days"]) + random.randint(-2, 5)
    expected_del  = po_date + timedelta(days=max(1, expected_days))
    actual_del    = expected_del + timedelta(days=random.randint(-2, 7))
    qty           = random.randint(100, 2000)
    delay_d       = max(0, (actual_del - expected_del).days)

    proc_list.append({
        "po_id":                  f"PO{str(i).zfill(5)}",
        "supplier_id":            prd["supplier_id"],
        "product_id":             prd["product_id"],
        "warehouse_id":           random.choice(list(warehouses["warehouse_id"])),
        "po_date":                po_date.strftime("%Y-%m-%d"),
        "expected_delivery_date": expected_del.strftime("%Y-%m-%d"),
        "actual_delivery_date":   actual_del.strftime("%Y-%m-%d"),
        "quantity_ordered":       qty,
        "quantity_received":      qty if delay_d <= 3
                                  else int(qty * random.uniform(0.85, 1.0)),
        "unit_cost":              prd["unit_cost"],
        "total_cost":             round(qty * prd["unit_cost"], 2),
        "status":                 random.choices(
            ["Pending", "In Transit", "Received", "Partial"],
            weights=[10, 15, 65, 10]
        )[0],
        "delay_days":             delay_d
    })

procurement = pd.DataFrame(proc_list)
procurement.to_csv(f"{OUTPUT_DIR}/procurement.csv", index=False)
print(f"✓ procurement.csv— {len(procurement)} rows")


# ─────────────────────────────────────────────
# 8. LOGISTICS / SHIPMENTS  (up to 300 rows)
# ─────────────────────────────────────────────
carriers = ["Blue Dart", "Delhivery", "Ecom Express",
            "XpressBees", "DTDC", "FedEx India", "Shadowfax"]

logistics_list = []
delivered_orders = orders[orders["status"] == "Delivered"]["order_id"].tolist()
shipped_orders   = orders[orders["status"].isin(["Shipped", "In Transit"])]["order_id"].tolist()
combined         = delivered_orders + shipped_orders
selected_orders  = random.sample(combined, min(300, len(combined)))

for i, oid in enumerate(selected_orders, 1):
    order_row  = orders[orders["order_id"] == oid].iloc[0]
    origin     = order_row["warehouse_id"]
    dest_city  = order_row["delivery_city"]
    distance   = random.randint(80, 2200)
    duration_h = round(distance / random.uniform(40, 80), 1)
    freight    = round(distance * random.uniform(0.8, 2.5), 2)

    logistics_list.append({
        "shipment_id":              f"SHP{str(i).zfill(5)}",
        "order_id":                 oid,
        "carrier":                  random.choice(carriers),
        "origin_warehouse_id":      origin,
        "destination_city":         dest_city,
        "dispatch_date":            order_row["ship_date"],
        "estimated_delivery_date":  order_row["delivery_date"],
        "actual_delivery_date":     order_row["delivery_date"],
        "distance_km":              distance,
        "transit_hours":            duration_h,
        "freight_cost":             freight,
        "shipment_status":          "Delivered" if order_row["status"] == "Delivered"
                                    else "In Transit",
        "is_delayed":               1 if random.random() < 0.18 else 0
    })

logistics = pd.DataFrame(logistics_list)
logistics.to_csv(f"{OUTPUT_DIR}/logistics.csv", index=False)
print(f"✓ logistics.csv  — {len(logistics)} rows")


# ─────────────────────────────────────────────
# 9. DEMAND_HISTORY  (monthly demand per product)
# Covers: Forecast Accuracy, Demand Variability KPIs
# ─────────────────────────────────────────────
demand_rows = []
for prd_id in products["product_id"]:
    base_demand = random.randint(200, 2000)
    for month in range(1, 13):
        # Seasonal factor: Oct-Nov festival spike, Apr-May slight dip
        seasonal = 1.0
        if month in [10, 11]:
            seasonal = random.uniform(1.3, 1.8)
        elif month in [4, 5]:
            seasonal = random.uniform(0.8, 1.1)
        actual_demand    = int(base_demand * seasonal * random.uniform(0.85, 1.15))
        forecasted       = int(actual_demand * random.uniform(0.88, 1.12))
        forecast_err_pct = round(
            abs(actual_demand - forecasted) / max(actual_demand, 1) * 100, 2
        )
        demand_rows.append({
            "demand_id":          None,
            "product_id":         prd_id,
            "year":               2024,
            "month":              month,
            "actual_demand":      actual_demand,
            "forecasted_demand":  forecasted,
            "forecast_error_pct": forecast_err_pct
        })

demand_history = pd.DataFrame(demand_rows)
demand_history["demand_id"] = range(1, len(demand_history) + 1)
demand_history.to_csv(f"{OUTPUT_DIR}/demand_history.csv", index=False)
print(f"✓ demand_history.csv — {len(demand_history)} rows")

print("\n✅ All datasets generated successfully.")
print("Next steps:")
print("  1. Run schema.sql in MySQL to create all tables & views")
print("  2. Run load_to_mysql.py to populate the database")
print("  3. (Optional) Run ml_models.py to generate ML prediction CSVs")
print("  4. Connect Power BI to MySQL using the views (vw_*) as data sources")
