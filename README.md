# Supply Chain Management – Centralized Monitoring System

A complete **Supply Chain Analytics Project** built using **Python, MySQL, Machine Learning, Power BI, and Dashboard Visualization**.

This project simulates a real-world retail/FMCG supply chain and helps monitor:

- Inventory levels
- Demand forecasting
- Stockout prediction
- Shipment delay prediction
- Supplier performance
- Warehouse operations
- KPI dashboards

## Tech Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- MySQL
- Streamlit

## Project Structure

```bash
scm-project/
│── data/
│   ├── generate_dataset.py
│   ├── suppliers.csv
│   ├── products.csv
│   ├── warehouses.csv
│   ├── inventory.csv
│   ├── orders.csv
│   ├── order_items.csv
│   ├── procurement.csv
│   ├── logistics.csv
│   └── demand_history.csv
│
│── database/
│   ├── schema.sql
│   └── load_to_mysql.py
│
│── ml/
│   ├── ml_models.py
│   ├── saved_models/
│   ├── demand_forecast.csv
│   ├── stockout_predictions.csv
│   ├── delay_predictions.csv
│   └── model_metrics.json
│
│── dashboard/
│   ├── dashboard.py
│
│── requirements.txt
│── README.md
```

## Steps to Run

### Prerequisites

- Python 3.10+
- MySQL 8.0+ running locally
- `pip` package manager

### 1. Clone / Set Up the Project

```bash
git clone https://github.com/YOUR_USERNAME/scm-project.git
cd scm-project
pip install -r requirements.txt
pip install streamlit        # For the dashboard
```

### 2. Set Up the MySQL Database

Make sure MySQL is running, then execute the schema:

```bash
mysql -u root -p < database/schema.sql
```

### 3. Generate the Dataset

```bash
python data/generate_dataset.py
```

### 4. Load Data into MySQL

Open `database/load_to_mysql.py` and update the password on line ~27:

```python
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YOUR_PASSWORD_HERE",   # ← update this
    "database": "scm_db"
}
```

Then run:

```bash
python database/load_to_mysql.py
```

### 5. Train the ML Models

Open `ml/ml_models.py` and update the MySQL password (same as above, around line ~45). Then:

```bash
python ml/ml_models.py
```

### 6. Launch the Dashboard

```bash
streamlit run dashboard/dashboard.py
```

Open your browser at `http://localhost:8501`.
