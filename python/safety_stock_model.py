"""
Supply Chain Control Tower: Safety Stock & Reorder Point (ROP) Model
Computes statistically rigorous safety buffers using lead-time and demand variance.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Tuple

from config import (
    DB_PATH,
    SERVICE_LEVEL_Z,
    DEFAULT_HOLDING_COST_PCT
)

# Type alias for the 4-DataFrame return from load_data
Tuple_Data = Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]


class SafetyStockModel:
    """
    Implements the classic stochastic inventory model with dual variability:
    SS = Z * sqrt( (L_bar * sigma_D^2) + (D_bar^2 * sigma_L^2) )
    ROP = (D_bar * L_bar) + SS
    """

    def __init__(self, db_path: str = str(DB_PATH), service_z: float = SERVICE_LEVEL_Z):
        self.db_path = db_path
        self.service_z = service_z

    def load_data(self) -> Tuple_Data:
        conn = sqlite3.connect(self.db_path)
        try:
            # Route lead-time statistics (Category x Shipping Mode x Market)
            lead_time_query = """
                SELECT 
                    p.category_name,
                    f.shipping_mode,
                    f.market,
                    COUNT(f.order_item_id) AS route_order_count,
                    AVG(f.days_real) AS avg_lead_time_days,
                    AVG(f.days_real * f.days_real) - (AVG(f.days_real) * AVG(f.days_real)) AS lead_time_variance
                FROM fact_orders f
                JOIN dim_products p ON f.product_id = p.product_id
                GROUP BY p.category_name, f.shipping_mode, f.market
            """
            df_route_lt = pd.read_sql_query(lead_time_query, conn)

            # Product daily demand aggregations (grouped by calendar date)
            product_demand_query = """
                SELECT 
                    p.product_id,
                    p.product_name,
                    p.category_name,
                    p.department_name,
                    p.product_price,
                    substr(f.order_date, 1, 10) AS order_day,
                    SUM(f.quantity_ordered) AS daily_units
                FROM fact_orders f
                JOIN dim_products p ON f.product_id = p.product_id
                GROUP BY p.product_id, p.product_name, p.category_name, p.department_name, p.product_price, substr(f.order_date, 1, 10)
            """
            df_product_daily = pd.read_sql_query(product_demand_query, conn)

            # Primary shipping route per product (mode and market with highest volume)
            primary_route_query = """
                WITH ranked_routes AS (
                    SELECT 
                        f.product_id,
                        f.shipping_mode,
                        f.market,
                        COUNT(*) AS order_cnt,
                        ROW_NUMBER() OVER (PARTITION BY f.product_id ORDER BY COUNT(*) DESC) AS rnk
                    FROM fact_orders f
                    GROUP BY f.product_id, f.shipping_mode, f.market
                )
                SELECT product_id, shipping_mode AS primary_shipping_mode, market AS primary_market
                FROM ranked_routes
                WHERE rnk = 1
            """
            df_primary_routes = pd.read_sql_query(primary_route_query, conn)

            # Join with ABC-XYZ classification if available
            abc_xyz_query = """
                SELECT 
                    product_id,
                    abc_class,
                    xyz_class,
                    abc_xyz_segment,
                    operational_priority,
                    risk_level
                FROM inventory_abc_xyz_analysis
            """
            try:
                df_abc_xyz = pd.read_sql_query(abc_xyz_query, conn)
            except Exception:
                df_abc_xyz = pd.DataFrame()

            return df_route_lt, df_product_daily, df_primary_routes, df_abc_xyz
        finally:
            conn.close()

    def calculate_model(self) -> pd.DataFrame:
        df_route_lt, df_product_daily, df_primary_routes, df_abc_xyz = self.load_data()

        # Clean lead time variance and standard deviation
        df_route_lt["lead_time_variance"] = df_route_lt["lead_time_variance"].apply(lambda v: max(0.0, v if pd.notnull(v) else 0.0))
        df_route_lt["std_lead_time_days"] = np.sqrt(df_route_lt["lead_time_variance"])
        # Minimum baseline standard deviation if route variance is near 0
        df_route_lt["std_lead_time_days"] = df_route_lt["std_lead_time_days"].apply(lambda s: max(0.5, s))

        # 1. Product Daily Demand Metrics
        demand_stats = df_product_daily.groupby(["product_id", "product_name", "category_name", "department_name", "product_price"]).agg(
            total_units=("daily_units", "sum"),
            active_days=("order_day", "nunique"),
            mean_daily_demand=("daily_units", "mean"),
            std_daily_demand=("daily_units", "std")
        ).reset_index()

        demand_stats["std_daily_demand"] = demand_stats["std_daily_demand"].fillna(0.0)

        # 2. Attach Primary Route
        product_master = demand_stats.merge(df_primary_routes, on="product_id", how="left")

        # 3. Attach Route Lead Time
        product_master = product_master.merge(
            df_route_lt[["category_name", "shipping_mode", "market", "avg_lead_time_days", "std_lead_time_days"]],
            left_on=["category_name", "primary_shipping_mode", "primary_market"],
            right_on=["category_name", "shipping_mode", "market"],
            how="left"
        )

        # Impute fallback lead time if route missing
        product_master["avg_lead_time_days"] = product_master["avg_lead_time_days"].fillna(4.0)
        product_master["std_lead_time_days"] = product_master["std_lead_time_days"].fillna(1.0)

        # 4. Safety Stock & Reorder Point Formulation
        # SS = Z * sqrt( (L_bar * sigma_D^2) + (D_bar^2 * sigma_L^2) )
        def compute_ss(row):
            L_bar = row["avg_lead_time_days"]
            s_L = row["std_lead_time_days"]
            D_bar = row["mean_daily_demand"]
            s_D = row["std_daily_demand"]

            inside = (L_bar * (s_D ** 2)) + ((D_bar ** 2) * (s_L ** 2))
            ss = self.service_z * np.sqrt(max(0.0, inside))
            return int(np.ceil(ss))

        product_master["safety_stock_units"] = product_master.apply(compute_ss, axis=1)

        # ROP = (D_bar * L_bar) + SS
        product_master["lead_time_demand_units"] = np.ceil(
            product_master["mean_daily_demand"] * product_master["avg_lead_time_days"]
        ).astype(int)

        product_master["reorder_point_units"] = (
            product_master["lead_time_demand_units"] + product_master["safety_stock_units"]
        ).astype(int)

        # 5. Inventory Cycle Simulation & Health Status
        # Seed deterministic stock simulation per SKU based on product_id
        np.random.seed(42)
        stock_multipliers = np.random.uniform(0.4, 2.5, size=len(product_master))
        product_master["current_stock_units"] = np.round(
            product_master["reorder_point_units"] * stock_multipliers
        ).astype(int)
        # Ensure at least 1 unit if product has active demand
        product_master["current_stock_units"] = product_master["current_stock_units"].clip(lower=1)

        # Dynamic Status Flag
        def evaluate_status(row):
            current = row["current_stock_units"]
            rop = row["reorder_point_units"]
            if current < rop:
                return "REORDER IMMEDIATELY"
            elif current > (2.2 * rop):
                return "OVERSTOCKED"
            else:
                return "OPTIMAL"

        product_master["stock_status"] = product_master.apply(evaluate_status, axis=1)

        # Financial Impact
        product_master["inventory_valuation"] = np.round(
            product_master["current_stock_units"] * product_master["product_price"], 2
        )
        product_master["annual_holding_cost"] = np.round(
            product_master["inventory_valuation"] * DEFAULT_HOLDING_COST_PCT, 2
        )
        
        # Excess working capital in overstocked items
        product_master["excess_stock_units"] = np.maximum(
            0, product_master["current_stock_units"] - (2 * product_master["reorder_point_units"])
        )
        product_master["excess_capital_tied_up"] = np.round(
            product_master["excess_stock_units"] * product_master["product_price"], 2
        )

        # Stockout shortage risk units on reorder items
        product_master["stockout_shortage_units"] = np.maximum(
            0, product_master["reorder_point_units"] - product_master["current_stock_units"]
        )
        product_master["stockout_revenue_at_risk"] = np.round(
            product_master["stockout_shortage_units"] * product_master["product_price"], 2
        )

        # Merge ABC-XYZ if present
        if not df_abc_xyz.empty:
            product_master = product_master.merge(
                df_abc_xyz[["product_id", "abc_class", "xyz_class", "abc_xyz_segment", "operational_priority", "risk_level"]],
                on="product_id",
                how="left"
            )

        # Round floats
        product_master["mean_daily_demand"] = product_master["mean_daily_demand"].round(2)
        product_master["std_daily_demand"] = product_master["std_daily_demand"].round(2)
        product_master["avg_lead_time_days"] = product_master["avg_lead_time_days"].round(2)
        product_master["std_lead_time_days"] = product_master["std_lead_time_days"].round(2)

        # Clean redundant columns from merge
        cols_to_drop = [c for c in ["shipping_mode", "market"] if c in product_master.columns]
        if cols_to_drop:
            product_master = product_master.drop(columns=cols_to_drop)

        return product_master

    def run(self) -> pd.DataFrame:
        df_master = self.calculate_model()
        conn = sqlite3.connect(self.db_path)
        try:
            df_master.to_sql("inventory_safety_stock_rop", conn, if_exists="replace", index=False)
        finally:
            conn.close()
        return df_master




if __name__ == "__main__":
    model = SafetyStockModel()
    results = model.run()
    print(f"Safety Stock model executed for {len(results)} products.")
    print("Status counts:")
    print(results["stock_status"].value_counts())

# dual-variance stochastic formula Z=1.65

# ROP = D_bar * L_bar + Safety_Stock

# edge case: zero lead-time variance floor

# dual-variance stochastic formula Z=1.65
