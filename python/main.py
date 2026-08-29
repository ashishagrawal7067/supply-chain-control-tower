"""
Supply Chain Control Tower: Master Pipeline Orchestrator
Executes the end-to-end analytics workflow:
1. ETL & Star Schema Normalization
2. SQL Analytical Views Compilation
3. Statistical ABC-XYZ Inventory Classification Engine
4. Stochastic Lead-Time & Demand Safety Stock / ROP Modeling
5. Executive OpenPyXL S&OP Workbook Generation
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RAW_CSV_PATH, DB_PATH, OUTPUT_EXCEL_PATH
from etl_loader import ETLLoader
from inventory_classifier import InventoryClassifier
from safety_stock_model import SafetyStockModel
from excel_builder import ExcelReportBuilder


def run_pipeline():
    start_time = time.time()
    print("=" * 80)
    print("      SUPPLY CHAIN CONTROL TOWER: END-TO-END ANALYTICS ENGINE")
    print("=" * 80)

    # 0. Pre-flight checks
    if not RAW_CSV_PATH.exists():
        print(f"ERROR: Raw dataset not found at {RAW_CSV_PATH}!")
        print("Please ensure DataCoSupplyChainDataset.csv is placed in the data/ directory.")
        sys.exit(1)

    # 1. ETL & Database Normalization
    print("\n>>> PHASE 1: ETL Pipeline, Star Schema Normalization & View Compilation")
    p1_start = time.time()
    loader = ETLLoader()
    loader.run()
    print(f"--- Phase 1 completed in {time.time() - p1_start:.2f}s ---\n")

    # 2. ABC-XYZ Inventory Classification
    print(">>> PHASE 2: ABC-XYZ Statistical Demand & Pareto Engine")
    p2_start = time.time()
    classifier = InventoryClassifier()
    df_classified = classifier.run()
    print(f"Classified {len(df_classified):,} products into 9-box S&OP quadrants.")
    print(f"--- Phase 2 completed in {time.time() - p2_start:.2f}s ---\n")

    # 3. Safety Stock & Reorder Point Optimization
    print(">>> PHASE 3: Lead-Time Variance & Safety Stock / ROP Modeling")
    p3_start = time.time()
    model = SafetyStockModel()
    df_modeled = model.run()
    print(f"Modeled dynamic safety stock and ROP for {len(df_modeled):,} products.")
    print(f"--- Phase 3 completed in {time.time() - p3_start:.2f}s ---\n")

    # 4. Automated Excel Deliverable Generation
    print(">>> PHASE 4: OpenPyXL Executive S&OP Control Tower Generation")
    p4_start = time.time()
    builder = ExcelReportBuilder()
    builder.generate()
    print(f"--- Phase 4 completed in {time.time() - p4_start:.2f}s ---\n")

    # Final Summary
    total_time = time.time() - start_time
    print("=" * 80)
    print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.2f} SECONDS!")
    print(f"Output Deliverable: {OUTPUT_EXCEL_PATH}")
    print(f"SQLite Database:    {DB_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()
