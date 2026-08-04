-- ==============================================================================
-- SUPPLY CHAIN CONTROL TOWER: DATA QUALITY & INTEGRITY AUDIT
-- Technology: SQLite / ANSI SQL compatible
-- Description: Diagnostic checks and audit suite for data sanitization & validation
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. NULL VALUE AUDIT: Key Operational & Financial Attributes
-- Identifies field completeness across dimensions and facts.
-- ------------------------------------------------------------------------------
SELECT 
    'fact_orders' AS table_name,
    COUNT(*) AS total_records,
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_order_ids,
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_ids,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_ids,
    SUM(CASE WHEN order_date IS NULL OR order_date = '' THEN 1 ELSE 0 END) AS null_order_dates,
    SUM(CASE WHEN sales_amount IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN profit_per_order IS NULL THEN 1 ELSE 0 END) AS null_profit,
    SUM(CASE WHEN days_scheduled IS NULL THEN 1 ELSE 0 END) AS null_scheduled_days,
    SUM(CASE WHEN days_real IS NULL THEN 1 ELSE 0 END) AS null_real_days
FROM fact_orders;

-- ------------------------------------------------------------------------------
-- 2. DUPLICATE KEY AUDIT
-- Checks uniqueness of primary keys and unexpected multi-item duplication.
-- ------------------------------------------------------------------------------
SELECT 
    order_item_id,
    COUNT(*) AS occurrence_count
FROM fact_orders
GROUP BY order_item_id
HAVING COUNT(*) > 1;

-- ------------------------------------------------------------------------------
-- 3. DOMAIN INTEGRITY & RANGE CONSTRAINTS
-- Identifies non-physical anomalies (e.g., negative prices, negative lead times).
-- ------------------------------------------------------------------------------
SELECT
    'Range & Logic Anomalies' AS audit_type,
    SUM(CASE WHEN quantity_ordered <= 0 THEN 1 ELSE 0 END) AS non_positive_quantities,
    SUM(CASE WHEN product_price <= 0 THEN 1 ELSE 0 END) AS non_positive_prices,
    SUM(CASE WHEN discount_rate < 0 OR discount_rate > 1 THEN 1 ELSE 0 END) AS invalid_discount_rates,
    SUM(CASE WHEN days_scheduled <= 0 THEN 1 ELSE 0 END) AS non_positive_scheduled_days,
    SUM(CASE WHEN days_real < 0 THEN 1 ELSE 0 END) AS negative_real_days,
    SUM(CASE WHEN sales_amount < 0 THEN 1 ELSE 0 END) AS negative_sales
FROM fact_orders;

-- ------------------------------------------------------------------------------
-- 4. DELIVERY STATUS CONCORDANCE AUDIT
-- Validates that recorded delivery status matches physical day metrics.
-- (Days Real > Days Scheduled should coincide with 'Late delivery' or late risk).
-- ------------------------------------------------------------------------------
SELECT
    delivery_status,
    late_delivery_risk,
    COUNT(*) AS record_count,
    ROUND(AVG(days_real - days_scheduled), 2) AS avg_delay_variance,
    MIN(days_real - days_scheduled) AS min_delay_variance,
    MAX(days_real - days_scheduled) AS max_delay_variance
FROM fact_orders
GROUP BY delivery_status, late_delivery_risk
ORDER BY delivery_status;

-- ------------------------------------------------------------------------------
-- 5. REFERENTIAL INTEGRITY (ORPHAN CHECKS)
-- Ensures all fact records resolve to valid parent dimension keys.
-- ------------------------------------------------------------------------------
SELECT 
    'Orphaned Fact Records' AS check_name,
    COUNT(f.order_item_id) AS orphan_count
FROM fact_orders f
LEFT JOIN dim_products p ON f.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT 
    'Orphaned Customer Records' AS check_name,
    COUNT(f.order_item_id) AS orphan_count
FROM fact_orders f
LEFT JOIN dim_customers c ON f.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
