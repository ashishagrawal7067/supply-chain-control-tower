# Supply Chain Control Tower: Executive S&OP Findings & Strategic Insights

## Executive Summary
This report synthesizes empirical findings from the end-to-end analytical evaluation of **DataCo Global Supply Chain Operations** (180,519 transactions across 3 years). The analysis investigates fulfillment accuracy (On-Time In-Full / OTIF), profit erosion due to shipping delays, and inventory allocation health using statistical ABC-XYZ demand classification and stochastic safety stock modeling.

---

## 1. Top Business Insights

### Finding 1: Systemic Fulfillment Breakdown & Expedited Shipping Failure
* **Overall OTIF Reliability:** Across all global markets and shipping modes, the enterprise achieves an **overall OTIF fulfillment rate of only 45.3%**, meaning that **54.7% (98,743 shipments) experience delivery delays**.
* **Expedited Service Collapse:** The most alarming operational breakdown occurs in premium shipping tiers:
  * **First Class Shipping:** Achieves **0.0% OTIF (100% late deliveries across 27,814 shipments)**, putting **$5,674,369.76** of sales at risk with an average delay of +1.00 days past scheduled fulfillment.
  * **Second Class Shipping:** Registers an **OTIF of only 20.27% (79.73% late delivery rate across 35,216 shipments)**, suffering an average delay of **+1.99 days** and putting **$5,698,215.87** at risk.
  * **Standard Class Shipping:** Fulfills 107,752 orders (59.69% of enterprise volume) at a **60.23% OTIF rate (39.77% late)**, putting **$8,736,398.09** at risk.
  * **Same Day Shipping:** The only flawless tier, fulfilling 9,737 shipments (5.39% volume) at **100.0% OTIF**.
* **Root Cause Analysis:** Premium tiers promise 1 to 3 day transit times without dedicated carrier capacity or priority sorting lanes, leading directly to carrier SLA breaches.

### Finding 2: Direct Profit Erosion & Late Delivery Revenue Exposure
* **The Financial Cost of Delay:** Deliveries fulfilled late generate **$20,108,983.71 in delayed revenue exposure** (54.7% of total enterprise sales of $36,784,735.01).
* **Margin Compression:** Average profit per order declines from **$22.27 on on-time deliveries** to **$21.73 on delayed orders**, driven by:
  * Customer service escalation and concession credits.
  * Return logistics handling and reverse supply chain transport.
  * Escalated freight charges incurred when attempting to expedite delayed parcels.

### Finding 3: Uniform Global Distribution Bottlenecks
* **Market-Level Delivery Parity:** Delays are not localized to a single geography—all global markets cluster near the ~45% OTIF threshold:
  * **Europe:** 50,252 orders | **44.98% OTIF** (Lowest fulfillment accuracy)
  * **Pacific Asia:** 41,260 orders | **45.10% OTIF**
  * **USCA:** 25,799 orders | **45.36% OTIF**
  * **LATAM:** 51,594 orders | **45.60% OTIF**
  * **Africa:** 11,614 orders | **45.92% OTIF**
* **Strategic Takeaway:** The bottleneck is systemic to the transportation management system (TMS) and carrier scheduling rules, rather than local port or customs delays.

### Finding 4: Extreme Pareto Revenue Concentration (ABC-XYZ)
Statistical segmentation of the 118 catalog products demonstrates intense revenue concentration:
* **The Core 8 ("AX" Superstars):** Exactly **8 Class A SKUs (6.8% of catalog)** generate **$31,165,252.26 (84.73% of enterprise revenue)**. All 8 items exhibit stable weekly demand ($CV \le 0.50$). These items are the financial engine of the enterprise and require automated JIT replenishment and dedicated buffer stock.
* **Class B Transitionals:** 16 SKUs generate **$3,811,381.30 (10.36% of sales)** across BX (1 SKU), BY (5 SKUs), and BZ (10 SKUs).
* **Long-Tail Exposure ("CZ" Obsolescence Candidates):** 18 SKUs fall into the erratic, low-value **CZ quadrant**, generating only $264,464.72 (0.72% of sales) across 3 years while consuming warehouse slotting and incurring holding costs.

### Finding 5: Reorder Point (ROP) Misalignment & Shortage Exposure
Running the stochastic safety stock formula ($SS = Z \times \sqrt{\bar{L}\sigma_D^2 + \bar{D}^2\sigma_L^2}$ with $Z=1.65$ for 95% cycle service level):
* **Immediate Reorder Deficit:** **36 SKUs (30.5% of catalog)** are operating below their safety reorder threshold, exposing the business to **$229,554.82 in immediate stockout shortage revenue risk**.
* **Overstocked Capital Drain:** **16 SKUs (13.6% of catalog)** have on-hand stock exceeding 220% of their ROP, trapping **$84,148.08 in excess working capital** and accruing $16,829.62 in annual carrying costs.
* **Optimal Band:** 66 SKUs (55.9% of catalog) maintain balanced buffer stock within the operational replenishment window.

---

## 2. Strategic Recommendations for S&OP Leadership

| # | Strategic Initiative | Target Area | Business Impact |
|---|---|---|---|
| **1** | **Eliminate or Restructure First/Second Class SLAs** | Logistics & Transportation | Either renegotiate dedicated carrier SLAs for First Class (currently 0% OTIF) or adjust promised customer delivery windows by +1 to +2 days to eliminate SLA default penalties and recover customer trust. |
| **2** | **Automated Replenishment for the 8 "AX" Superstars** | Inventory Management | Transition the 8 Class A SKUs ($31.2M revenue) to Vendor Managed Inventory (VMI) or automated continuous review $(s, Q)$ with guaranteed safety buffers. |
| **3** | **Emergency Purchase Orders for 36 Deficit SKUs** | Procurement & Purchasing | Issue immediate replenishment orders for the 36 SKUs identified in Sheet 5 (`SKU_Reorder_Simulator`) to eliminate $229.5K in stockout revenue at risk. |
| **4** | **SKU Rationalization for 18 "CZ" Items** | Merchandising & Warehousing | Markdown, bundle, or decommission the 18 CZ long-tail items, liberating $84K+ in trapped inventory capital and freeing high-velocity warehouse racking. |
| **5** | **Adopt Executive S&OP Excel Control Tower** | Cross-Functional Leadership | Implement `Supply_Chain_Control_Tower.xlsx` as the weekly operational artifact for cross-functional consensus between Sales, Logistics, and Finance. |

---

## 3. Assumptions & Methodology Governance
1. **Lead Time Modeling:** Lead time parameters ($\bar{L}, \sigma_L$) are modeled at the Category × Shipping Mode × Market route granularity to reflect empirical carrier transit distributions.
2. **Cycle Service Level:** Formulated at a 95% cycle service level ($Z = 1.65$), representing enterprise S&OP best practice.
3. **Holding Cost Rate:** Standard 20.0% annual holding cost benchmark applied to assess inventory carrying drag.
4. **Data Sanitization:** 100% PII fields stripped during Phase 1 ETL to maintain strict GDPR/enterprise governance compliance.
