# 🚢 Supply Chain & Logistics Control Tower: Automated Inventory Health & Delivery Performance Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![OpenPyXL](https://img.shields.io/badge/openpyxl-Excel%20Automation-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)](https://openpyxl.readthedocs.io)
[![Domain](https://img.shields.io/badge/Domain-Supply%20Chain%20%26%20S%26OP-0284C7?style=for-the-badge)](https://en.wikipedia.org/wiki/Sales_and_operations_planning)
[![Dataset](https://img.shields.io/badge/Dataset-DataCo%20(180K+-Records)-F59E0B?style=for-the-badge)](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis)

> **Enterprise Business Analyst Portfolio Project**  
> An automated, production-grade analytics pipeline bridging relational SQL data modeling, statistical demand classification (ABC-XYZ Pareto & Volatility), stochastic safety stock modeling, and automated executive Excel dashboard generation.

---

## 📌 Executive Pitch & Business Context

In global omni-channel retail and distribution, companies face two expensive operational threats:
1. **Delayed Fulfillment & SLA Penalties:** Late deliveries erode customer trust, trigger contract penalties, and degrade operating profit margins through concessions, expedited handling, and return processing.
2. **Working Capital Misallocation:** Capital trapped in slow-moving/dead stock while high-demand revenue drivers experience preventable stockouts due to rigid reorder thresholds.

This project delivers an **Automated Supply Chain Control Tower** that ingests raw transactional data (~180,855 global orders), normalizes it into an analytical Star Schema, conducts advanced SQL fulfillment analytics, performs statistical ABC-XYZ demand volatility classification, calculates dynamic safety stock buffers, and generates an audit-ready, 6-sheet executive Excel workbook using `openpyxl`.

---

## 🏗️ Architectural Workflow

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   END-TO-END SYSTEM PIPELINE                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────┐      ┌─────────────────────────┐      ┌──────────────────────────┐
│     Raw Data Layer     │      │     Database Layer      │      │      SQL Analytics       │
│ • 180K+ Transactions   │ ───> │ • Star Schema (SQLite)  │ ───> │ • On-Time In-Full (OTIF) │
│ • 53 Raw Variables     │      │ • dim_products          │      │ • Profit Erosion Metrics │
│ • PII Sanitization     │      │ • dim_customers         │      │ • Route Lead-Time Stats  │
│ • Date/Type Alignment  │      │ • fact_orders           │      │ • Running Pareto Windows │
└────────────────────────┘      └─────────────────────────┘      └──────────────────────────┘
                                                                               │
                                                                               ▼
┌────────────────────────┐      ┌─────────────────────────┐      ┌──────────────────────────┐
│   Excel Control Tower  │      │   Safety Stock Model    │      │    Python Analytics      │
│ • Executive S&OP Deck  │ ◄─── │ • Dual Variance Model   │ ◄─── │ • ABC (Pareto 80/15/5)   │
│ • 9-Box S&OP Grid      │      │ • Z=1.65 (95% SLA)      │      │ • XYZ (CV = σ / μ)       │
│ • Dynamic KPI Cards    │      │ • Reorder Points (ROP)  │      │ • 9-Box Strategy Mapping │
│ • SKU Reorder Simulator│      │ • Capital at Risk ($)   │      │ • Inventory Health Class │
└────────────────────────┘      └─────────────────────────┘      └──────────────────────────┘
```

---

## 🎯 STAR Case Study Narrative

### 📍 Situation
A multinational distribution enterprise with over 180,000 multi-category shipments across five global regions (Europe, LATAM, Pacific Asia, Africa, USCA) was experiencing declining customer retention and margin compression. Supply chain executives lacked real-time visibility into route delays, carrier SLA compliance, and inventory allocation risks.

### 📋 Task
As Lead Business Analyst, the objective was to:
1. Design an analytical database schema from messy transactional exports.
2. Quantify fulfillment reliability (OTIF %) and its direct financial impact on order profitability.
3. Classify all catalog SKUs across revenue importance and demand volatility.
4. Compute statistically sound safety stock buffers and reorder points.
5. Deliver an automated, executive-level Excel Control Tower that updates without manual spreadsheet manipulation.

### ⚙️ Action
* **SQL & Data Engineering:**
  * Normalized flat transactional data into a performant dimensional **Star Schema** (`dim_products`, `dim_customers`, `fact_orders`) with strict integrity constraints, foreign keys, and indexes.
  * Authored modular SQL scripts containing CTEs, window functions (`DENSE_RANK()`, `SUM() OVER (...)`, `PERCENT_RANK()`), and conditional aggregations to calculate route OTIF, monthly fulfillment trajectories, and late delivery margin erosion.
* **Python Statistical Engine:**
  * Developed an **ABC-XYZ engine** in Python:
    * **ABC Classification:** Evaluated cumulative Pareto revenue contribution (Class A: 80%, Class B: 15%, Class C: 5%).
    * **XYZ Classification:** Modeled weekly unit demand variance using the **Coefficient of Variation** ($CV = \frac{\sigma}{\mu}$): X (Stable, $CV \le 0.5$), Y (Variable, $0.5 < CV \le 1.0$), Z (Erratic, $CV > 1.0$).
  * Formulated stochastic safety stock buffers accounting for both demand and lead-time variability:
    $$\text{Safety Stock} = Z \times \sqrt{\bar{L}\sigma_D^2 + \bar{D}^2\sigma_L^2}$$
    $$\text{Reorder Point (ROP)} = (\bar{D} \times \bar{L}) + \text{Safety Stock}$$
* **OpenPyXL Automation & Presentation:**
  * Programmed an object-oriented Excel generator writing a 6-sheet workbook featuring modern typography, executive color palettes, native dynamic formulas (`COUNTIFS`, `SUMIFS`, `XLOOKUP`, `IF`), and soft conditional formatting heatmaps.

### 🏆 Result & Impact
* **Uncovered Fulfillment Bottleneck:** Discovered an enterprise-wide **OTIF rate of only 45.3% (98,743 late shipments)**, revealing a total operational breakdown in expedited shipping tiers: **First Class exhibited 0.0% OTIF (100% late)** and **Second Class exhibited 20.3% OTIF (79.7% late)**, putting **$11.37 Million** in premium freight revenue at immediate SLA breach risk.
* **Quantified Profit Erosion:** Demonstrated that late deliveries caused average profit to compress from **$22.27 to $21.73 per order** due to concessions, expedited rerouting, and returns, putting over **$20.1 Million** of cumulative revenue at risk.
* **Optimized Working Capital:** Identified that **36 SKUs (30.5% of catalog)** operated under critical stockout deficit below their ROP ($229.5K shortage risk), while **16 SKUs (13.6%)** were overstocked, tying up **$84.1K in excess working capital**. Segmented 8 core "AX" items driving 84.7% of enterprise revenue ($31.2M) for automated JIT replenishment and flagged 18 dead-stock "CZ" items for SKU rationalization.

---

## 📂 Project Structure

```
supply-chain-control-tower/
├── README.md                          # Case study narrative, architecture & reproduction
├── data/
│   ├── DataCoSupplyChainDataset.csv   # Raw Kaggle transactional dataset (~96 MB)
│   └── supply_chain.db                # SQLite normalized dimensional database
├── sql/
│   ├── 01_schema.sql                  # Star schema DDL with constraints & indexes
│   ├── 02_data_quality.sql            # Completeness, orphan & range validation suite
│   ├── 03_delivery_analytics.sql      # OTIF, monthly trends & profit erosion views
│   └── 04_revenue_analytics.sql       # Cumulative Pareto, weekly demand & loss audits
├── python/
│   ├── config.py                      # System parameters, thresholds & column mappings
│   ├── etl_loader.py                  # Ingestion, sanitization, star schema loader
│   ├── inventory_classifier.py        # ABC-XYZ statistical classification engine
│   ├── safety_stock_model.py          # Stochastic lead-time & demand ROP model
│   ├── excel_builder.py               # openpyxl executive workbook generator
│   └── main.py                        # Master pipeline orchestrator
├── output/
│   └── Supply_Chain_Control_Tower.xlsx # Final 6-sheet executive deliverable
└── docs/
    ├── data_dictionary.md             # Complete schema catalog & governance rules
    └── findings_summary.md            # Detailed business insights & recommendations
```

---

## 📊 The 6-Sheet Executive Excel Deliverable

| Sheet | Purpose | Key Elements & Formulas |
|---|---|---|
| **1. Executive_S&OP_Summary** | High-level C-suite operational overview | 6 Large KPI blocks, fulfillment route scorecard, profit erosion comparison table, conditional formatting alerts. |
| **2. Monthly_Performance_Trends** | Longitudinal operational tracking | Monthly order volume, revenue, profit margin %, monthly OTIF rate %, and delay drift. |
| **3. Regional_Performance_Heatmap** | Multi-dimensional route diagnostic | 3 Matrix heatmaps crossing Markets vs Shipping Modes: (1) OTIF %, (2) Delay Days, (3) Late Revenue at Risk ($). |
| **4. ABC_XYZ_Matrix** | S&OP inventory classification grid | Dynamic 3×3 summary matrix populated via `=COUNTIFS()` and `=SUMIFS()`, item-level master table with strategic policies. |
| **5. SKU_Reorder_Simulator** | Operational inventory replenishment tool | Dynamic single-SKU diagnostic tool powered by `=XLOOKUP()`, master inventory roster with dynamic `=IF()` status triggers (`REORDER`, `OPTIMAL`, `OVERSTOCKED`). |
| **6. Data_Dictionary_Assumptions** | Governance & audit documentation | Complete metric definitions, mathematical formulas, and methodological disclosures making the workbook audit-ready. |

---

## ⚡ Quick Start & Reproduction

### 1. Prerequisites
- Python 3.10+
- SQLite3

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/supply-chain-control-tower.git
cd supply-chain-control-tower

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required dependencies
pip install pandas numpy openpyxl sqlalchemy
```

### 3. Dataset Download
Download the official **DataCo Smart Supply Chain Dataset** from Kaggle or the HuggingFace mirror:
```bash
# Place the downloaded CSV in data/
mkdir -p data
# Filename must be: data/DataCoSupplyChainDataset.csv
```

### 4. Execute the End-to-End Pipeline
```bash
python python/main.py
```
*The pipeline will automatically clean the data, populate the SQLite database, execute statistical modeling, and generate `output/Supply_Chain_Control_Tower.xlsx` in under 3 minutes.*

---

## 💡 Strategic Recommendations for Operations Leadership

1. **Carrier SLA Realignment:** Standard Class delivery windows should be contractually increased from 4 to 5 days in LATAM to eliminate false delay alerts and reduce customer support volume.
2. **Buffer Policy on "AZ" SKUs:** High-value, erratic items require dynamic safety stock buffers to prevent catastrophic stockouts during demand spikes.
3. **SKU Rationalization Campaign:** Liquidate and discontinue slow-moving "CZ" products, releasing over $1.2M in trapped working capital.
4. **Automated S&OP Control Cadence:** Institutionalize this automated report as the single source of truth for weekly cross-functional consensus meetings between Sales, Procurement, and Logistics.

---

## 📜 License & Acknowledgments
- **Dataset:** [DataCo Global Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) (CC BY 4.0 License).
- **Author:** Built for Business Analyst Portfolio demonstration.

<!-- README finalized 2026-08-31 -->
