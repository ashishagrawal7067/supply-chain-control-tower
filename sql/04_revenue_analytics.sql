-- ==============================================================================
-- SUPPLY CHAIN CONTROL TOWER: REVENUE & INVENTORY DEMAND ANALYTICS
-- Technology: SQLite / ANSI SQL compatible
-- Description: Window-function driven financial aggregations, weekly demand
--              trajectories, and cumulative Pareto percentiles.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- VIEW 1: v_category_revenue_ranked
-- Cumulative revenue share and volume ranking per merchandising category.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_category_revenue_ranked;
CREATE VIEW v_category_revenue_ranked AS
WITH category_totals AS (
    SELECT 
        p.department_name,
        p.category_name,
        COUNT(f.order_item_id) AS total_units_sold,
        ROUND(SUM(f.sales_amount), 2) AS category_revenue,
        ROUND(SUM(f.profit_per_order), 2) AS category_profit,
        ROUND(AVG(f.discount_rate) * 100.0, 2) AS avg_discount_pct
    FROM fact_orders f
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.department_name, p.category_name
),
grand_total AS (
    SELECT SUM(category_revenue) AS enterprise_revenue FROM category_totals
)
SELECT 
    c.department_name,
    c.category_name,
    c.total_units_sold,
    c.category_revenue,
    c.category_profit,
    c.avg_discount_pct,
    ROUND(100.0 * c.category_revenue / g.enterprise_revenue, 2) AS revenue_share_pct,
    ROUND(100.0 * SUM(c.category_revenue) OVER (ORDER BY c.category_revenue DESC) / g.enterprise_revenue, 2) AS cumulative_revenue_pct,
    DENSE_RANK() OVER (ORDER BY c.category_revenue DESC) AS revenue_rank
FROM category_totals c
CROSS JOIN grand_total g;

-- ------------------------------------------------------------------------------
-- VIEW 2: v_product_revenue_pareto
-- Running Pareto curve per product for foundational ABC input validation.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_product_revenue_pareto;
CREATE VIEW v_product_revenue_pareto AS
WITH product_totals AS (
    SELECT 
        p.product_id,
        p.product_name,
        p.category_name,
        p.department_name,
        p.product_price,
        COUNT(f.order_item_id) AS order_lines_count,
        SUM(f.quantity_ordered) AS total_units_ordered,
        ROUND(SUM(f.sales_amount), 2) AS total_revenue,
        ROUND(SUM(f.profit_per_order), 2) AS total_profit
    FROM fact_orders f
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category_name, p.department_name, p.product_price
),
enterprise_totals AS (
    SELECT SUM(total_revenue) AS total_enterprise_sales FROM product_totals
)
SELECT 
    p.product_id,
    p.product_name,
    p.category_name,
    p.department_name,
    p.product_price,
    p.order_lines_count,
    p.total_units_ordered,
    p.total_revenue,
    p.total_profit,
    ROUND(100.0 * p.total_revenue / e.total_enterprise_sales, 4) AS revenue_pct_of_total,
    ROUND(100.0 * SUM(p.total_revenue) OVER (ORDER BY p.total_revenue DESC) / e.total_enterprise_sales, 2) AS cumulative_revenue_pct,
    CASE 
        WHEN (100.0 * SUM(p.total_revenue) OVER (ORDER BY p.total_revenue DESC) / e.total_enterprise_sales) <= 80.0 THEN 'A'
        WHEN (100.0 * SUM(p.total_revenue) OVER (ORDER BY p.total_revenue DESC) / e.total_enterprise_sales) <= 95.0 THEN 'B'
        ELSE 'C'
    END AS sql_abc_class
FROM product_totals p
CROSS JOIN enterprise_totals e;

-- ------------------------------------------------------------------------------
-- VIEW 3: v_product_weekly_demand
-- Aggregates unit velocity on a weekly basis to compute demand variance.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_product_weekly_demand;
CREATE VIEW v_product_weekly_demand AS
SELECT 
    f.product_id,
    p.product_name,
    p.category_name,
    strftime('%Y-%W', f.order_date) AS order_year_week,
    SUM(f.quantity_ordered) AS weekly_units,
    ROUND(SUM(f.sales_amount), 2) AS weekly_sales,
    COUNT(f.order_item_id) AS weekly_order_count
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY f.product_id, p.product_name, p.category_name, strftime('%Y-%W', f.order_date);

-- ------------------------------------------------------------------------------
-- VIEW 4: v_loss_making_products_audit
-- Pinpoints SKUs generating negative aggregate profit due to aggressive discounting
-- or high late-order returns.
-- ------------------------------------------------------------------------------
DROP VIEW IF EXISTS v_loss_making_products_audit;
CREATE VIEW v_loss_making_products_audit AS
SELECT 
    p.product_id,
    p.product_name,
    p.category_name,
    COUNT(f.order_item_id) AS total_orders,
    ROUND(SUM(f.sales_amount), 2) AS total_sales,
    ROUND(SUM(f.profit_per_order), 2) AS net_profit,
    ROUND(AVG(f.discount_rate) * 100.0, 2) AS avg_discount_pct,
    SUM(CASE WHEN f.profit_per_order < 0 THEN 1 ELSE 0 END) AS negative_profit_order_count,
    ROUND(100.0 * SUM(CASE WHEN f.profit_per_order < 0 THEN 1 ELSE 0 END) / COUNT(f.order_item_id), 2) AS loss_order_pct
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category_name
HAVING SUM(f.profit_per_order) < 0 OR (100.0 * SUM(CASE WHEN f.profit_per_order < 0 THEN 1 ELSE 0 END) / COUNT(f.order_item_id)) > 25.0
ORDER BY net_profit ASC;

-- fix Pareto boundary edge case
