-- ==============================================================================
-- SUPPLY CHAIN CONTROL TOWER: DELIVERY & FULFILLMENT ANALYTICS
-- Technology: SQLite / ANSI SQL compatible
-- Description: Core analytical views for On-Time-In-Full (OTIF), delay trends,
--              carrier/mode performance, and late delivery profit erosion.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- VIEW 1: v_otif_by_route
-- Fulfillment accuracy (OTIF %) and delay variance across Market & Shipping Mode.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_otif_by_route;
CREATE VIEW v_otif_by_route AS
SELECT 
    market,
    shipping_mode,
    COUNT(order_item_id) AS total_orders,
    SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END) AS on_time_orders,
    SUM(CASE WHEN days_real > days_scheduled THEN 1 ELSE 0 END) AS late_orders,
    ROUND(100.0 * SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END) / COUNT(order_item_id), 2) AS otif_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN days_real > days_scheduled THEN 1 ELSE 0 END) / COUNT(order_item_id), 2) AS late_rate_pct,
    ROUND(AVG(days_scheduled), 2) AS avg_scheduled_days,
    ROUND(AVG(days_real), 2) AS avg_real_days,
    ROUND(AVG(days_real - days_scheduled), 2) AS avg_delay_days,
    ROUND(SUM(sales_amount), 2) AS total_route_sales,
    ROUND(SUM(CASE WHEN days_real > days_scheduled THEN sales_amount ELSE 0 END), 2) AS late_revenue_at_risk
FROM fact_orders
GROUP BY market, shipping_mode;

-- ------------------------------------------------------------------------------
-- VIEW 2: v_monthly_delivery_trends
-- Chronological performance tracking: identifies seasonal delays and OTIF drift.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_monthly_delivery_trends;
CREATE VIEW v_monthly_delivery_trends AS
SELECT 
    substr(order_date, 1, 7) AS order_year_month,
    COUNT(order_item_id) AS total_orders,
    ROUND(SUM(sales_amount), 2) AS total_sales,
    ROUND(SUM(profit_per_order), 2) AS total_profit,
    SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END) AS on_time_orders,
    SUM(CASE WHEN days_real > days_scheduled THEN 1 ELSE 0 END) AS late_orders,
    ROUND(100.0 * SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END) / COUNT(order_item_id), 2) AS monthly_otif_pct,
    ROUND(AVG(days_real - days_scheduled), 2) AS avg_delay_days,
    ROUND(SUM(CASE WHEN days_real > days_scheduled THEN sales_amount ELSE 0 END), 2) AS monthly_late_revenue
FROM fact_orders
GROUP BY substr(order_date, 1, 7)
ORDER BY order_year_month;

-- ------------------------------------------------------------------------------
-- VIEW 3: v_customer_segment_fulfillment
-- Segment-level SLA delivery rates ranked by service reliability.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_customer_segment_fulfillment;
CREATE VIEW v_customer_segment_fulfillment AS
WITH segment_metrics AS (
    SELECT 
        c.customer_segment,
        COUNT(f.order_item_id) AS total_orders,
        ROUND(SUM(f.sales_amount), 2) AS total_revenue,
        ROUND(SUM(f.profit_per_order), 2) AS total_profit,
        SUM(CASE WHEN f.days_real <= f.days_scheduled THEN 1 ELSE 0 END) AS on_time_count,
        SUM(CASE WHEN f.days_real > f.days_scheduled THEN 1 ELSE 0 END) AS late_count,
        ROUND(100.0 * SUM(CASE WHEN f.days_real <= f.days_scheduled THEN 1 ELSE 0 END) / COUNT(f.order_item_id), 2) AS otif_rate_pct,
        ROUND(AVG(f.days_real - f.days_scheduled), 2) AS avg_delay_days
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.customer_segment
)
SELECT 
    customer_segment,
    total_orders,
    total_revenue,
    total_profit,
    on_time_count,
    late_count,
    otif_rate_pct,
    avg_delay_days,
    DENSE_RANK() OVER (ORDER BY otif_rate_pct ASC) AS worst_fulfillment_rank
FROM segment_metrics;

-- ------------------------------------------------------------------------------
-- VIEW 4: v_late_delivery_cost_impact
-- Evaluates the profit erosion and margin compression on late deliveries vs on-time.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_late_delivery_cost_impact;
CREATE VIEW v_late_delivery_cost_impact AS
WITH performance_split AS (
    SELECT 
        market,
        CASE WHEN days_real <= days_scheduled THEN 'On-Time' ELSE 'Late' END AS delivery_category,
        COUNT(order_item_id) AS order_volume,
        ROUND(SUM(sales_amount), 2) AS total_sales,
        ROUND(SUM(profit_per_order), 2) AS total_profit,
        ROUND(AVG(profit_per_order), 2) AS avg_profit_per_order,
        ROUND(100.0 * SUM(profit_per_order) / SUM(sales_amount), 2) AS profit_margin_pct
    FROM fact_orders
    GROUP BY market, CASE WHEN days_real <= days_scheduled THEN 'On-Time' ELSE 'Late' END
)
SELECT 
    o.market,
    o.order_volume AS on_time_volume,
    l.order_volume AS late_volume,
    o.total_sales AS on_time_sales,
    l.total_sales AS late_sales_at_risk,
    o.avg_profit_per_order AS on_time_avg_profit,
    l.avg_profit_per_order AS late_avg_profit,
    ROUND(o.avg_profit_per_order - l.avg_profit_per_order, 2) AS profit_erosion_per_order,
    o.profit_margin_pct AS on_time_margin_pct,
    l.profit_margin_pct AS late_margin_pct,
    ROUND(o.profit_margin_pct - l.profit_margin_pct, 2) AS margin_compression_pct
FROM performance_split o
JOIN performance_split l ON o.market = l.market AND o.delivery_category = 'On-Time' AND l.delivery_category = 'Late';

-- ------------------------------------------------------------------------------
-- VIEW 5: v_lead_time_route_distribution
-- Lead time statistics (mean and variance) by Market & Shipping Mode.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_lead_time_route_distribution;
CREATE VIEW v_lead_time_route_distribution AS
SELECT 
    f.market,
    f.shipping_mode,
    COUNT(*) AS sample_size,
    ROUND(AVG(f.days_real), 2) AS avg_lead_time_days,
    MIN(f.days_real) AS min_lead_time_days,
    MAX(f.days_real) AS max_lead_time_days,
    ROUND(AVG((f.days_real - sub.mean_days) * (f.days_real - sub.mean_days)), 3) AS lead_time_variance
FROM fact_orders f
JOIN (
    SELECT market, shipping_mode, AVG(days_real) AS mean_days
    FROM fact_orders
    GROUP BY market, shipping_mode
) sub ON f.market = sub.market AND f.shipping_mode = sub.shipping_mode
GROUP BY f.market, f.shipping_mode;


-- route lead-time stats view

-- profit erosion view added
