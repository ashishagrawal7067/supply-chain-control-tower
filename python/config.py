"""
Supply Chain Control Tower: Configuration & Operational Parameters
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SQL_DIR = BASE_DIR / "sql"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Database & File Targets
DB_PATH = DATA_DIR / "supply_chain.db"
SQLITE_URL = f"sqlite:///{DB_PATH}"
RAW_CSV_PATH = DATA_DIR / "DataCoSupplyChainDataset.csv"
OUTPUT_EXCEL_PATH = OUTPUT_DIR / "Supply_Chain_Control_Tower.xlsx"

# SQL Script Paths
SQL_SCHEMA = SQL_DIR / "01_schema.sql"
SQL_DATA_QUALITY = SQL_DIR / "02_data_quality.sql"
SQL_DELIVERY = SQL_DIR / "03_delivery_analytics.sql"
SQL_REVENUE = SQL_DIR / "04_revenue_analytics.sql"

# ABC Classification Parameters (Pareto Revenue Share)
ABC_CLASS_A_THRESHOLD = 0.80  # Top 80% of cumulative enterprise revenue
ABC_CLASS_B_THRESHOLD = 0.95  # Next 15% (80% - 95%)
# Remainder (95% - 100%) is Class C

# XYZ Classification Parameters (Demand Coefficient of Variation = sigma / mu)
XYZ_STABLE_MAX_CV = 0.50     # X: CV <= 0.50 (Highly predictable demand)
XYZ_VARIABLE_MAX_CV = 1.00   # Y: 0.50 < CV <= 1.00 (Moderate variability)
# Z: CV > 1.00 (Erratic / lumpy demand or low observation count)

# Safety Stock & Inventory Optimization Parameters
SERVICE_LEVEL_Z = 1.65       # 95% cycle service level normal distribution z-score
MIN_OBSERVATIONS_FOR_XYZ = 4  # Minimum distinct weekly periods required for statistical reliability
DEFAULT_HOLDING_COST_PCT = 0.20 # 20% annual inventory holding cost rate

# Raw Data Column Normalization Mapping
RAW_TO_STANDARDIZED_COLUMNS = {
    "Type": "transaction_type",
    "Days for shipping (real)": "days_real",
    "Days for shipment (scheduled)": "days_scheduled",
    "Benefit per order": "profit_per_order",
    "Sales per customer": "sales_per_customer",
    "Delivery Status": "delivery_status",
    "Late_delivery_risk": "late_delivery_risk",
    "Category Id": "category_id",
    "Category Name": "category_name",
    "Customer City": "customer_city",
    "Customer Country": "customer_country",
    "Customer Id": "customer_id",
    "Customer Segment": "customer_segment",
    "Customer State": "customer_state",
    "Customer Zipcode": "customer_zipcode",
    "Department Id": "department_id",
    "Department Name": "department_name",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Market": "market",
    "Order City": "order_city",
    "Order Country": "order_country",
    "Order Customer Id": "order_customer_id",
    "order date (DateOrders)": "order_date",
    "Order Date (DateOrders)": "order_date",
    "Order Id": "order_id",
    "Order Item Cardprod Id": "product_card_id",
    "Order Item Discount": "discount_amount",
    "Order Item Discount Rate": "discount_rate",
    "Order Item Id": "order_item_id",
    "Order Item Profit Ratio": "profit_ratio",
    "Order Item Quantity": "quantity_ordered",
    "Sales": "sales_amount",
    "Order Item Total": "order_item_total",
    "Order Profit Per Order": "order_profit_per_order",
    "Order Region": "order_region",
    "Order State": "order_state",
    "Order Status": "order_status",
    "Product Card Id": "product_id",
    "Product Category Id": "product_category_id",
    "Product Name": "product_name",
    "Product Price": "product_price",
    "shipping date (DateOrders)": "shipping_date",
    "Shipping Date (DateOrders)": "shipping_date",
    "Shipping Mode": "shipping_mode"
}

# Unnecessary / High PII columns to drop during ETL
COLUMNS_TO_DROP = [
    "Customer Email",
    "Customer Password",
    "Customer Fname",
    "Customer Lname",
    "Customer Street",
    "Product Description",
    "Product Image",
    "Product Status"
]
