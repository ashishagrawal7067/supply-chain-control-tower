"""
Supply Chain Control Tower: Automated ETL Pipeline & Data Sanitization Engine
Extracts flat CSV, performs rigorous data cleansing, loads Star Schema in SQLite,
and executes analytical views and data quality assertions.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from config import (
    DB_PATH,
    RAW_CSV_PATH,
    SQL_SCHEMA,
    SQL_DATA_QUALITY,
    SQL_DELIVERY,
    SQL_REVENUE,
    RAW_TO_STANDARDIZED_COLUMNS,
    COLUMNS_TO_DROP
)


class ETLLoader:
    """
    Orchestrates CSV Ingestion, Schema Normalization, and Data Quality Auditing.
    """

    def __init__(self, raw_csv_path: Path = RAW_CSV_PATH, db_path: Path = DB_PATH):
        self.raw_csv_path = raw_csv_path
        self.db_path = db_path
        self.audit_summary: Dict[str, Any] = {}

    def extract_and_clean(self) -> pd.DataFrame:
        """Loads raw CSV and applies sanitization and type conversions."""
        print(f"Reading raw transactional data from {self.raw_csv_path}...")
        
        # DataCo dataset typically requires latin-1 / cp1252 encoding
        try:
            df = pd.read_csv(self.raw_csv_path, encoding="latin-1")
        except UnicodeDecodeError:
            df = pd.read_csv(self.raw_csv_path, encoding="cp1252")

        initial_rows, initial_cols = df.shape
        print(f"Raw dataset shape: {initial_rows:,} records, {initial_cols} columns.")

        # 1. Drop PII and non-analytical attributes
        existing_drops = [c for c in COLUMNS_TO_DROP if c in df.columns]
        df = df.drop(columns=existing_drops)

        # 2. Standardize column names
        rename_map = {k: v for k, v in RAW_TO_STANDARDIZED_COLUMNS.items() if k in df.columns}
        df = df.rename(columns=rename_map)

        # 3. Clean and parse date columns
        for date_col in ["order_date", "shipping_date"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

        # 4. Remove duplicate line items if present
        if "order_item_id" in df.columns:
            dupe_count = df.duplicated(subset=["order_item_id"]).sum()
            if dupe_count > 0:
                print(f"Removing {dupe_count:,} duplicate order line items...")
                df = df.drop_duplicates(subset=["order_item_id"])

        # 5. Handle missing values
        if "customer_zipcode" in df.columns:
            df["customer_zipcode"] = df["customer_zipcode"].fillna("UNKNOWN").astype(str)

        # 6. Physical and operational constraints validation
        # Ensure positive quantities and non-negative sales
        df["quantity_ordered"] = df["quantity_ordered"].apply(lambda q: max(1, int(q) if pd.notnull(q) else 1))
        df["product_price"] = df["product_price"].apply(lambda p: max(0.01, float(p) if pd.notnull(p) else 0.01))
        df["sales_amount"] = df["sales_amount"].apply(lambda s: max(0.0, float(s) if pd.notnull(s) else 0.0))
        df["days_real"] = df["days_real"].apply(lambda d: max(0, int(d) if pd.notnull(d) else 0))
        df["days_scheduled"] = df["days_scheduled"].apply(lambda d: max(1, int(d) if pd.notnull(d) else 1))
        
        # Computed fulfillment delay
        df["delay_days"] = df["days_real"] - df["days_scheduled"]

        # Ensure late_delivery_risk is strictly binary
        df["late_delivery_risk"] = df["late_delivery_risk"].apply(lambda r: 1 if r in [1, "1", True] else 0)

        # Align delivery status string
        df["delivery_status"] = df["delivery_status"].fillna("Unknown")

        # Ensure NOT NULL schema columns have no nulls
        if "profit_per_order" in df.columns:
            df["profit_per_order"] = df["profit_per_order"].fillna(0.0)
        if "discount_rate" in df.columns:
            df["discount_rate"] = df["discount_rate"].fillna(0.0)
        if "discount_amount" in df.columns:
            df["discount_amount"] = df["discount_amount"].fillna(0.0)
        if "order_status" in df.columns:
            df["order_status"] = df["order_status"].fillna("UNKNOWN")
        if "shipping_mode" in df.columns:
            df["shipping_mode"] = df["shipping_mode"].fillna("Standard Class")
        if "market" in df.columns:
            df["market"] = df["market"].fillna("UNKNOWN")
        if "order_region" in df.columns:
            df["order_region"] = df["order_region"].fillna("UNKNOWN")

        self.audit_summary = {
            "initial_rows": initial_rows,
            "cleaned_rows": len(df),
            "columns_retained": len(df.columns),
            "dropped_columns": len(existing_drops)
        }
        return df

    def initialize_database(self):
        """Initializes tables using DDL schema script."""
        print(f"Initializing database schema at {self.db_path}...")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            with open(SQL_SCHEMA, "r", encoding="utf-8") as f:
                schema_ddl = f.read()
            conn.executescript(schema_ddl)
            conn.commit()
        finally:
            conn.close()

    def load_star_schema(self, df: pd.DataFrame):
        """Loads normalized dimension and fact tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            print("Populating dim_products dimension...")
            dim_prod_cols = [
                "product_id", "product_name", "category_id", "category_name",
                "department_id", "department_name", "product_price"
            ]
            df_products = df[[c for c in dim_prod_cols if c in df.columns]].drop_duplicates(subset=["product_id"])
            df_products.to_sql("dim_products", conn, if_exists="append", index=False)

            print("Populating dim_customers dimension...")
            dim_cust_cols = [
                "customer_id", "customer_segment", "customer_city",
                "customer_state", "customer_country", "customer_zipcode"
            ]
            df_customers = df[[c for c in dim_cust_cols if c in df.columns]].drop_duplicates(subset=["customer_id"])
            df_customers.to_sql("dim_customers", conn, if_exists="append", index=False)

            print("Populating fact_orders table (this may take a few seconds)...")
            fact_cols = [
                "order_item_id", "order_id", "order_date", "shipping_date",
                "product_id", "customer_id", "market", "order_region",
                "order_city", "order_country", "shipping_mode", "order_status",
                "quantity_ordered", "product_price", "discount_rate", "discount_amount",
                "sales_amount", "profit_per_order", "profit_ratio",
                "days_scheduled", "days_real", "delay_days", "delivery_status",
                "late_delivery_risk"
            ]
            df_fact = df[[c for c in fact_cols if c in df.columns]]
            df_fact.to_sql("fact_orders", conn, if_exists="append", index=False, chunksize=10000)

            conn.commit()
            print(f"Star schema loaded: {len(df_products):,} products, {len(df_customers):,} customers, {len(df_fact):,} order items.")
        finally:
            conn.close()

    def build_views(self):
        """Executes analytical views for delivery and revenue analysis."""
        print("Compiling SQL analytics views...")
        conn = sqlite3.connect(self.db_path)
        try:
            for sql_file in [SQL_DELIVERY, SQL_REVENUE]:
                with open(sql_file, "r", encoding="utf-8") as f:
                    script = f.read()
                conn.executescript(script)
            conn.commit()
            print("All analytical views compiled successfully.")
        finally:
            conn.close()

    def run_data_quality_audit(self) -> pd.DataFrame:
        """Executes data quality checks and outputs scorecard."""
        print("Running data quality & integrity checks...")
        conn = sqlite3.connect(self.db_path)
        try:
            audit_queries = {
                "Null Fact Check": "SELECT COUNT(*) as records, SUM(CASE WHEN sales_amount IS NULL THEN 1 ELSE 0 END) as null_sales FROM fact_orders;",
                "Orphan Products": "SELECT COUNT(*) as orphans FROM fact_orders f LEFT JOIN dim_products p ON f.product_id = p.product_id WHERE p.product_id IS NULL;",
                "Orphan Customers": "SELECT COUNT(*) as orphans FROM fact_orders f LEFT JOIN dim_customers c ON f.customer_id = c.customer_id WHERE c.customer_id IS NULL;",
                "Negative Quantities": "SELECT COUNT(*) as invalid_qty FROM fact_orders WHERE quantity_ordered <= 0;",
                "OTIF Overall Summary": "SELECT COUNT(*) as total_orders, ROUND(100.0 * SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END)/COUNT(*), 2) as otif_pct FROM fact_orders;"
            }
            results = []
            for check_name, query in audit_queries.items():
                cur = conn.cursor()
                cur.execute(query)
                row = cur.fetchone()
                results.append({"Check Name": check_name, "Result": str(row)})
            
            df_audit = pd.DataFrame(results)
            print("Data Quality Scorecard:")
            for _, r in df_audit.iterrows():
                print(f"  - {r['Check Name']}: {r['Result']}")
            return df_audit
        finally:
            conn.close()

    def run(self):
        """Full ETL execution."""
        df = self.extract_and_clean()
        self.initialize_database()
        self.load_star_schema(df)
        self.build_views()
        self.run_data_quality_audit()
        print("ETL Pipeline completed successfully!")


if __name__ == "__main__":
    loader = ETLLoader()
    loader.run()

# date normalization pass v2

# dim_products and dim_customers loader added

# fact_orders loading with FK validation

# date normalization pass v2

# dim_products and dim_customers loader

# fact_orders loading with FK validation
