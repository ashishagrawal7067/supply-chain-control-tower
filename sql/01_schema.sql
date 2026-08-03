-- ==============================================================================
-- SUPPLY CHAIN CONTROL TOWER: DATABASE SCHEMA (STAR SCHEMA)
-- Technology: SQLite / ANSI SQL compatible
-- Description: DDL for Enterprise Supply Chain & Logistics Operations
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. DIMENSION: dim_products
-- Captures product hierarchy, merchandising departments, and baseline unit price.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_products;
CREATE TABLE dim_products (
    product_id          INTEGER PRIMARY KEY,
    product_name        TEXT NOT NULL,
    category_id         INTEGER,
    category_name       TEXT NOT NULL,
    department_id       INTEGER,
    department_name     TEXT NOT NULL,
    product_price       REAL NOT NULL CHECK (product_price >= 0),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_products_category ON dim_products(category_name);
CREATE INDEX idx_dim_products_department ON dim_products(department_name);

-- ------------------------------------------------------------------------------
-- 2. DIMENSION: dim_customers
-- Captures customer demographics, geography, and enterprise market segment.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_customers;
CREATE TABLE dim_customers (
    customer_id         INTEGER PRIMARY KEY,
    customer_segment    TEXT NOT NULL,
    customer_city       TEXT,
    customer_state      TEXT,
    customer_country    TEXT,
    customer_zipcode    TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_customers_segment ON dim_customers(customer_segment);
CREATE INDEX idx_dim_customers_country ON dim_customers(customer_country);

-- ------------------------------------------------------------------------------
-- 3. FACT TABLE: fact_orders
-- Granularity: One row per order line item.
-- Captures commercial transaction value, shipping timelines, fulfillment delay,
-- and profitability metrics.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders (
    order_item_id       INTEGER PRIMARY KEY,
    order_id            INTEGER NOT NULL,
    order_date          TEXT NOT NULL,
    shipping_date       TEXT,
    product_id          INTEGER NOT NULL,
    customer_id         INTEGER NOT NULL,
    market              TEXT NOT NULL,
    order_region        TEXT NOT NULL,
    order_city          TEXT,
    order_country       TEXT,
    shipping_mode       TEXT NOT NULL,
    order_status        TEXT NOT NULL,
    quantity_ordered    INTEGER NOT NULL CHECK (quantity_ordered > 0),
    product_price       REAL NOT NULL,
    discount_rate       REAL NOT NULL DEFAULT 0.0,
    discount_amount     REAL NOT NULL DEFAULT 0.0,
    sales_amount        REAL NOT NULL,
    profit_per_order    REAL NOT NULL,
    profit_ratio        REAL,
    days_scheduled      INTEGER NOT NULL,
    days_real           INTEGER NOT NULL,
    delay_days          INTEGER NOT NULL,
    delivery_status     TEXT NOT NULL,
    late_delivery_risk  INTEGER NOT NULL CHECK (late_delivery_risk IN (0, 1)),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
);

CREATE INDEX idx_fact_orders_order_id ON fact_orders(order_id);
CREATE INDEX idx_fact_orders_product_id ON fact_orders(product_id);
CREATE INDEX idx_fact_orders_customer_id ON fact_orders(customer_id);
CREATE INDEX idx_fact_orders_date ON fact_orders(order_date);
CREATE INDEX idx_fact_orders_market_mode ON fact_orders(market, shipping_mode);
CREATE INDEX idx_fact_orders_delivery_status ON fact_orders(delivery_status);
