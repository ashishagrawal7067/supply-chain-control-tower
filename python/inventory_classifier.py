"""
Supply Chain Control Tower: Inventory ABC-XYZ Classification Engine
Performs dual-dimensional Pareto revenue analysis and demand volatility modeling.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

from config import (
    DB_PATH,
    ABC_CLASS_A_THRESHOLD,
    ABC_CLASS_B_THRESHOLD,
    XYZ_STABLE_MAX_CV,
    XYZ_VARIABLE_MAX_CV,
    MIN_OBSERVATIONS_FOR_XYZ
)

# Business recommendation lookup per 9-box segment
SEGMENT_STRATEGIES = {
    "AX": {
        "priority": "HIGH",
        "risk_level": "LOW",
        "strategy": "Automate Replenishment (JIT)",
        "policy": "High-value stable demand. Implement automated continuous review (s, Q), optimize batch sizes, establish Vendor Managed Inventory (VMI)."
    },
    "AY": {
        "priority": "HIGH",
        "risk_level": "MEDIUM",
        "strategy": "Close Monitoring & Seasonal Buffer",
        "policy": "High-value seasonal or shifting demand. Implement dynamic safety stock, bi-weekly S&OP review, and responsive replenishment agreements."
    },
    "AZ": {
        "priority": "CRITICAL RISK",
        "risk_level": "HIGH",
        "strategy": "Active Management / Make-to-Order",
        "policy": "High-value erratic demand. Substantial capital at risk. Keep lean base stock with agile supplier lead times, or adopt make-to-order where feasible."
    },
    "BX": {
        "priority": "MEDIUM",
        "risk_level": "LOW",
        "strategy": "Standard Periodic Replenishment",
        "policy": "Moderate-value stable demand. Automated monthly reorder points, economic order quantity (EOQ) optimization."
    },
    "BY": {
        "priority": "MEDIUM",
        "risk_level": "MEDIUM",
        "strategy": "Periodic S&OP Review",
        "policy": "Moderate-value variable demand. Monthly buffer reviews, track promotional spikes and lead-time variability."
    },
    "BZ": {
        "priority": "MEDIUM-HIGH RISK",
        "risk_level": "HIGH",
        "strategy": "Inventory Rationalization",
        "policy": "Moderate-value erratic demand. Limit batch quantities, evaluate vendor MOQ, maintain conservative safety stock."
    },
    "CX": {
        "priority": "LOW",
        "risk_level": "LOW",
        "strategy": "Bulk Order / High MOQ",
        "policy": "Low-value stable demand. Infrequent bulk ordering to minimize handling and ordering transactions."
    },
    "CY": {
        "priority": "LOW",
        "risk_level": "LOW-MEDIUM",
        "strategy": "Standard Reorder Tolerances",
        "policy": "Low-value variable demand. Wide safety tolerances, low management touchpoint."
    },
    "CZ": {
        "priority": "PURGE / MONITOR",
        "risk_level": "HIGH (OBSOLESCENCE)",
        "strategy": "Obsolescence Review / Rationalize",
        "policy": "Low-value erratic demand. High likelihood of stock obsolescence and trapped working capital. Evaluate SKU rationalization, purge or markdown."
    }
}


class InventoryClassifier:
    """
    Orchestrates ABC (Revenue Pareto) and XYZ (Demand Volatility) classification.
    """

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path

    def load_product_demand(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Loads product revenue aggregations and weekly time-series from SQLite."""
        conn = sqlite3.connect(self.db_path)
        try:
            revenue_query = """
                SELECT 
                    p.product_id,
                    p.product_name,
                    p.category_name,
                    p.department_name,
                    p.product_price,
                    COUNT(f.order_item_id) AS total_orders,
                    SUM(f.quantity_ordered) AS total_units_sold,
                    ROUND(SUM(f.sales_amount), 2) AS total_revenue,
                    ROUND(SUM(f.profit_per_order), 2) AS total_profit,
                    ROUND(AVG(f.discount_rate) * 100.0, 2) AS avg_discount_pct
                FROM fact_orders f
                JOIN dim_products p ON f.product_id = p.product_id
                GROUP BY p.product_id, p.product_name, p.category_name, p.department_name, p.product_price
            """
            df_revenue = pd.read_sql_query(revenue_query, conn)

            weekly_query = """
                SELECT 
                    product_id,
                    strftime('%Y-%W', order_date) AS order_year_week,
                    SUM(quantity_ordered) AS weekly_quantity,
                    ROUND(SUM(sales_amount), 2) AS weekly_sales
                FROM fact_orders
                GROUP BY product_id, strftime('%Y-%W', order_date)
            """
            df_weekly = pd.read_sql_query(weekly_query, conn)

            return df_revenue, df_weekly
        finally:
            conn.close()

    def compute_abc_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes Pareto cumulative revenue share and assigns A, B, or C class.
        """
        df = df.copy()
        df = df.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
        total_enterprise_revenue = df["total_revenue"].sum()

        if total_enterprise_revenue == 0:
            df["revenue_share_pct"] = 0.0
            df["cumulative_revenue_pct"] = 0.0
            df["abc_class"] = "C"
            return df

        df["revenue_share_pct"] = (df["total_revenue"] / total_enterprise_revenue) * 100.0
        df["cumulative_revenue_pct"] = df["revenue_share_pct"].cumsum()

        df["prev_cum_pct"] = df["cumulative_revenue_pct"].shift(1, fill_value=0.0)

        # Class boundaries based on prior cumulative revenue share
        def assign_abc(prev_cum):
            if prev_cum < (ABC_CLASS_A_THRESHOLD * 100.0):
                return "A"
            elif prev_cum < (ABC_CLASS_B_THRESHOLD * 100.0):
                return "B"
            else:
                return "C"

        df["abc_class"] = df["prev_cum_pct"].apply(assign_abc)
        df = df.drop(columns=["prev_cum_pct"])
        return df

    def compute_xyz_classification(self, df_weekly: pd.DataFrame) -> pd.DataFrame:
        """
        Computes Coefficient of Variation (CV = sigma / mu) for weekly unit demand.
        Assigns X (Stable), Y (Variable), or Z (Erratic).
        """
        stats = df_weekly.groupby("product_id")["weekly_quantity"].agg(
            observations="count",
            mean_demand="mean",
            std_demand="std"
        ).reset_index()

        # Fill NaN std (e.g. single observation) with 0
        stats["std_demand"] = stats["std_demand"].fillna(0.0)

        # CV = std / mean
        def calculate_cv(row):
            if row["observations"] < MIN_OBSERVATIONS_FOR_XYZ:
                return 9.99  # Insufficient history forces Z
            if row["mean_demand"] <= 0:
                return 9.99
            return row["std_demand"] / row["mean_demand"]

        stats["demand_cv"] = stats.apply(calculate_cv, axis=1)

        def assign_xyz(row):
            if row["observations"] < MIN_OBSERVATIONS_FOR_XYZ:
                return "Z"
            cv = row["demand_cv"]
            if cv <= XYZ_STABLE_MAX_CV:
                return "X"
            elif cv <= XYZ_VARIABLE_MAX_CV:
                return "Y"
            else:
                return "Z"

        stats["xyz_class"] = stats.apply(assign_xyz, axis=1)
        return stats

    def run(self) -> pd.DataFrame:
        """Executes full classification pipeline and writes results back to SQLite."""
        df_revenue, df_weekly = self.load_product_demand()

        df_abc = self.compute_abc_classification(df_revenue)
        df_xyz = self.compute_xyz_classification(df_weekly)

        # Merge ABC and XYZ
        merged = df_abc.merge(df_xyz, on="product_id", how="left")

        # Fill missing XYZ for products with no weekly history
        merged["observations"] = merged["observations"].fillna(0).astype(int)
        merged["mean_demand"] = merged["mean_demand"].fillna(0.0)
        merged["std_demand"] = merged["std_demand"].fillna(0.0)
        merged["demand_cv"] = merged["demand_cv"].fillna(9.99)
        merged["xyz_class"] = merged["xyz_class"].fillna("Z")

        # Create combined 9-box segment (e.g. 'AX', 'BY', 'CZ')
        merged["abc_xyz_segment"] = merged["abc_class"] + merged["xyz_class"]

        # Add strategic recommendation columns
        merged["operational_priority"] = merged["abc_xyz_segment"].apply(
            lambda s: SEGMENT_STRATEGIES.get(s, {}).get("priority", "N/A")
        )
        merged["risk_level"] = merged["abc_xyz_segment"].apply(
            lambda s: SEGMENT_STRATEGIES.get(s, {}).get("risk_level", "N/A")
        )
        merged["recommended_strategy"] = merged["abc_xyz_segment"].apply(
            lambda s: SEGMENT_STRATEGIES.get(s, {}).get("strategy", "N/A")
        )
        merged["inventory_policy"] = merged["abc_xyz_segment"].apply(
            lambda s: SEGMENT_STRATEGIES.get(s, {}).get("policy", "N/A")
        )

        # Round numeric metrics for presentation
        merged["revenue_share_pct"] = merged["revenue_share_pct"].round(2)
        merged["cumulative_revenue_pct"] = merged["cumulative_revenue_pct"].round(2)
        merged["mean_demand"] = merged["mean_demand"].round(2)
        merged["std_demand"] = merged["std_demand"].round(2)
        merged["demand_cv"] = merged["demand_cv"].round(3)

        # Write to SQLite
        conn = sqlite3.connect(self.db_path)
        try:
            merged.to_sql("inventory_abc_xyz_analysis", conn, if_exists="replace", index=False)
        finally:
            conn.close()

        return merged


if __name__ == "__main__":
    classifier = InventoryClassifier()
    df_results = classifier.run()
    print(f"Classification completed: {len(df_results)} products classified.")
    print("Segment distribution:")
    print(df_results["abc_xyz_segment"].value_counts().sort_index())

# ABC Pareto 80/15/5 thresholds

# XYZ coefficient of variation CV model

# 9-box matrix strategy policy labels

# ABC Pareto 80/15/5 thresholds
