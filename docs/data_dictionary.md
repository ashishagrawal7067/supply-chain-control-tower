# Data Dictionary & Schema Governance Catalog

## Overview
This catalog documents the data architecture, entity relationships, schema attributes, and governance rules for the **Supply Chain Control Tower** project.

---

## 1. Dimensional Star Schema Architecture

The dataset is ingested from the flat transactional DataCo dataset (~180,855 records) and normalized into an analytical star schema optimized for SQL analytics and inventory modeling.

```
       ┌────────────────────────┐             ┌─────────────────────────┐
       │      dim_products       │             │      dim_customers      │
       ├────────────────────────┤             ├─────────────────────────┤
       │ PK  product_id         │◄──────┐      │ PK  customer_id         │◄─────┐
       │     product_name       │       │      │     customer_segment    │      │
       │     category_id        │       │      │     customer_city       │      │
       │     category_name      │       │      │     customer_state      │      │
       │     department_id      │       │      │     customer_country    │      │
       │     department_name    │       │      │     customer_zipcode    │      │
       │     product_price      │       │      └─────────────────────────┘      │
       └────────────────────────┘       │                                       │
                                        │                                       │
                               ┌────────┴───────────────────────────────────────┴──┐
                               │                    fact_orders                    │
                               ├───────────────────────────────────────────────────┤
                               │ PK  order_item_id                                 │
                               │     order_id                                      │
                               │     order_date                                    │
                               │     shipping_date                                 │
                               │ FK  product_id                                    │
                               │ FK  customer_id                                   │
                               │     market                                        │
                               │     order_region                                  │
                               │     order_city                                    │
                               │     order_country                                 │
                               │     shipping_mode                                 │
                               │     order_status                                  │
                               │     quantity_ordered                              │
                               │     product_price                                 │
                               │     discount_rate                                 │
                               │     discount_amount                               │
                               │     sales_amount                                  │
                               │     profit_per_order                              │
                               │     profit_ratio                                  │
                               │     days_scheduled                                │
                               │     days_real                                     │
                               │     delay_days                                    │
                               │     delivery_status                               │
                               │     late_delivery_risk                            │
                               └───────────────────────────────────────────────────┘
```

---

## 2. Table Specifications & Attribute Definitions

### 2.1 Dimension: `dim_products`
Captures unique merchandise items, product hierarchies, and baseline unit prices.

| Column | Data Type | Constraint | Description |
|---|---|---|---|
| `product_id` | `INTEGER` | PRIMARY KEY | Unique identifier for the catalog SKU (source: `Product Card Id`). |
| `product_name` | `TEXT` | NOT NULL | Commercial catalog title of the product. |
| `category_id` | `INTEGER` | NULLABLE | Numerical category taxonomy key. |
| `category_name` | `TEXT` | NOT NULL | Product grouping (e.g., *Cleats*, *Water Sports*, *Cardio Equipment*). |
| `department_id` | `INTEGER` | NULLABLE | Merchandising department taxonomy key. |
| `department_name` | `TEXT` | NOT NULL | Top-level division (e.g., *Fan Shop*, *Apparel*, *Golf*, *Footwear*). |
| `product_price` | `REAL` | CHECK (>= 0) | Standard catalog selling price per unit. |

---

### 2.2 Dimension: `dim_customers`
Captures buyer demographic characteristics and geographical attributes.

| Column | Data Type | Constraint | Description |
|---|---|---|---|
| `customer_id` | `INTEGER` | PRIMARY KEY | Unique enterprise customer identifier. |
| `customer_segment` | `TEXT` | NOT NULL | Market segment classification: `Consumer`, `Corporate`, or `Home Office`. |
| `customer_city` | `TEXT` | NULLABLE | Registered customer residence city. |
| `customer_state` | `TEXT` | NULLABLE | Registered customer state / province code. |
| `customer_country` | `TEXT` | NULLABLE | Registered country of customer residence. |
| `customer_zipcode` | `TEXT` | NULLABLE | Postal zip code (imputed with `'UNKNOWN'` if missing). |

---

### 2.3 Fact Table: `fact_orders`
Contains transactional order line details, commercial value, shipping execution timelines, and delivery performance.

| Column | Data Type | Constraint | Description |
|---|---|---|---|
| `order_item_id` | `INTEGER` | PRIMARY KEY | Unique identifier for the transaction line item. |
| `order_id` | `INTEGER` | NOT NULL | Order header identifier (an order may contain multiple item lines). |
| `order_date` | `TEXT` | NOT NULL | Timestamp of purchase transaction formatted as `YYYY-MM-DD HH:MM:SS`. |
| `shipping_date` | `TEXT` | NULLABLE | Timestamp when order was dispatched by the distribution center. |
| `product_id` | `INTEGER` | FK (`dim_products`) | Reference to catalog product. |
| `customer_id` | `INTEGER` | FK (`dim_customers`) | Reference to purchasing customer. |
| `market` | `TEXT` | NOT NULL | Regional commercial market: `Europe`, `LATAM`, `Pacific Asia`, `Africa`, `USCA`. |
| `order_region` | `TEXT` | NOT NULL | Specific geographic sub-region (e.g., *Western Europe*, *Central America*). |
| `order_city` | `TEXT` | NULLABLE | Destination delivery city. |
| `order_country` | `TEXT` | NULLABLE | Destination delivery country. |
| `shipping_mode` | `TEXT` | NOT NULL | Carrier delivery tier: `Standard Class`, `First Class`, `Second Class`, `Same Day`. |
| `order_status` | `TEXT` | NOT NULL | Operational status: `COMPLETE`, `PENDING`, `PROCESSING`, `CANCELED`, etc. |
| `quantity_ordered` | `INTEGER` | CHECK (> 0) | Number of units purchased in this order line. |
| `product_price` | `REAL` | NOT NULL | Price per item applied to this order line. |
| `discount_rate` | `REAL` | DEFAULT 0.0 | Promotional discount applied as a fraction (e.g., `0.15` for 15%). |
| `discount_amount` | `REAL` | DEFAULT 0.0 | Total dollar deduction resulting from discount rate. |
| `sales_amount` | `REAL` | NOT NULL | Net top-line invoice revenue (`quantity * price - discount`). |
| `profit_per_order` | `REAL` | NOT NULL | Net profit generated on this specific transaction line item. |
| `profit_ratio` | `REAL` | NULLABLE | Net margin ratio (`profit_per_order / sales_amount`). |
| `days_scheduled` | `INTEGER` | NOT NULL | Contracted / estimated delivery duration in calendar days. |
| `days_real` | `INTEGER` | NOT NULL | Actual measured delivery duration in calendar days from order to delivery. |
| `delay_days` | `INTEGER` | NOT NULL | Delivery delay variance: `days_real - days_scheduled`. |
| `delivery_status` | `TEXT` | NOT NULL | Carrier delivery status: `Late delivery`, `Shipping on time`, `Advance shipping`, `Shipping canceled`. |
| `late_delivery_risk` | `INTEGER` | CHECK (IN (0, 1)) | Flag (`1` = Late risk present, `0` = On-time / early). |

---

## 3. Data Cleansing & Governance Rationale

### 3.1 Pruned Columns (Dropped during ETL)
To protect data privacy (GDPR / CCPA) and remove non-analytical redundant fields:
1. **`Customer Email` & `Customer Password`:** Highly sensitive PII and mock password hashes that pose a security risk.
2. **`Customer Fname` & `Customer Lname`:** Redundant personal identifiers; analysis is conducted at the customer segment and geographic levels.
3. **`Customer Street`:** Excessive granularity not required for macro logistics modeling.
4. **`Product Description` & `Product Image`:** Web media placeholders that bloat database footprint without analytical value.
5. **`Product Status`:** Fully redundant with transaction line item status.

### 3.2 Imputations & Type Conversions
- **Date Formatting:** Converted from heterogeneous date strings to unified ISO 8601 strings (`YYYY-MM-DD HH:MM:SS`).
- **Null Postal Codes:** Imputed missing values with `'UNKNOWN'` to preserve record completeness.
- **Negative & Zero Bounds:** Enforced positive quantity (`>= 1`) and non-negative sales.

---

## 4. Analytical Derived Tables

### 4.1 Table: `inventory_abc_xyz_analysis`
Created by `inventory_classifier.py` to store statistical classifications:
- `revenue_share_pct`: Product sales as % of total enterprise sales.
- `cumulative_revenue_pct`: Running cumulative sales percentage.
- `abc_class`: `'A'` (Top 80%), `'B'` (Next 15%), `'C'` (Bottom 5%).
- `demand_cv`: Coefficient of variation ($\sigma / \mu$) of weekly unit sales.
- `xyz_class`: `'X'` ($\le 0.50$), `'Y'` ($0.50 < CV \le 1.00$), `'Z'` ($> 1.00$).
- `abc_xyz_segment`: Combined 9-box quadrant (e.g., `'AX'`, `'AY'`, `'AZ'`).
- `operational_priority`, `recommended_strategy`, `inventory_policy`: Strategic business directives.

### 4.2 Table: `inventory_safety_stock_rop`
Created by `safety_stock_model.py`:
- `mean_daily_demand`: Average unit velocity per calendar day.
- `std_daily_demand`: Standard deviation of daily demand.
- `avg_lead_time_days`: Mean delivery transit duration for the product's primary route.
- `std_lead_time_days`: Standard deviation of route transit duration.
- `safety_stock_units`: Statistically buffered stock: $Z \times \sqrt{\bar{L}\sigma_D^2 + \bar{D}^2\sigma_L^2}$.
- `reorder_point_units`: Inventory reorder trigger: $(\bar{D} \times \bar{L}) + \text{Safety Stock}$.
- `stock_status`: `'REORDER IMMEDIATELY'`, `'OPTIMAL'`, or `'OVERSTOCKED'`.
- `excess_capital_tied_up`: Dollar value tied up in inventory exceeding 220% of ROP.
- `stockout_revenue_at_risk`: Potential unfulfilled demand on SKUs with on-hand stock below ROP.
