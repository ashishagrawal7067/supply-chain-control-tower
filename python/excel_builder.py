"""
Supply Chain Control Tower: Executive Excel Deliverable Builder
Uses openpyxl to generate a multi-sheet, C-suite grade Sales & Operations Planning (S&OP)
workbook featuring KPI blocks, dynamic formulas (COUNTIFS, SUMIFS, XLOOKUP), conditional formatting,
and mathematical inventory modeling.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule

from config import (
    DB_PATH,
    OUTPUT_EXCEL_PATH,
    SERVICE_LEVEL_Z,
    DEFAULT_HOLDING_COST_PCT
)


# ------------------------------------------------------------------------------
# DESIGN SYSTEM: EXECUTIVE COLOR PALETTE & TYPOGRAPHY
# ------------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"

# Colors (Hex codes for openpyxl)
COLOR_NAVY_DARK = "0F172A"     # Slate 900
COLOR_NAVY_PRIMARY = "1E293B"  # Slate 800
COLOR_NAVY_ACCENT = "334155"   # Slate 700
COLOR_CARD_BG = "F8FAFC"       # Slate 50
COLOR_WHITE = "FFFFFF"
COLOR_MUTED_TEXT = "64748B"    # Slate 500
COLOR_BORDER = "CBD5E1"        # Slate 300
COLOR_BORDER_LIGHT = "E2E8F0"  # Slate 200

# Status & KPI Colors
COLOR_SUCCESS_BG = "DCFCE7"    # Green 100
COLOR_SUCCESS_FG = "15803D"    # Green 700
COLOR_WARNING_BG = "FEF3C7"    # Amber 100
COLOR_WARNING_FG = "B45309"    # Amber 700
COLOR_DANGER_BG = "FEE2E2"     # Red 100
COLOR_DANGER_FG = "B91C1C"     # Red 700
COLOR_BLUE_BG = "DBEAFE"       # Blue 100
COLOR_BLUE_FG = "1D4ED8"       # Blue 700

# Styles
font_title = Font(name=FONT_FAMILY, size=16, bold=True, color=COLOR_WHITE)
font_subtitle = Font(name=FONT_FAMILY, size=10, italic=True, color="94A3B8")
font_section_header = Font(name=FONT_FAMILY, size=12, bold=True, color=COLOR_NAVY_PRIMARY)
font_table_header = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_WHITE)
font_regular = Font(name=FONT_FAMILY, size=10, color=COLOR_NAVY_PRIMARY)
font_regular_bold = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_NAVY_PRIMARY)
font_kpi_value = Font(name=FONT_FAMILY, size=20, bold=True, color=COLOR_NAVY_PRIMARY)
font_kpi_label = Font(name=FONT_FAMILY, size=9, bold=True, color=COLOR_MUTED_TEXT)
font_kpi_sub = Font(name=FONT_FAMILY, size=8, italic=True, color=COLOR_MUTED_TEXT)

fill_title = PatternFill(start_color=COLOR_NAVY_DARK, end_color=COLOR_NAVY_DARK, fill_type="solid")
fill_table_header = PatternFill(start_color=COLOR_NAVY_PRIMARY, end_color=COLOR_NAVY_PRIMARY, fill_type="solid")
fill_zebra = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
fill_card = PatternFill(start_color=COLOR_CARD_BG, end_color=COLOR_CARD_BG, fill_type="solid")
fill_kpi_accent_blue = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
fill_kpi_accent_green = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
fill_kpi_accent_amber = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
fill_kpi_accent_red = PatternFill(start_color="EF4444", end_color="EF4444", fill_type="solid")

thin_border_side = Side(border_style="thin", color=COLOR_BORDER)
border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
border_kpi_card = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)


class ExcelReportBuilder:
    """
    Constructs the 6-sheet executive supply chain workbook.
    """

    def __init__(self, db_path: Path = DB_PATH, output_path: Path = OUTPUT_EXCEL_PATH):
        self.db_path = db_path
        self.output_path = output_path
        self.wb = openpyxl.Workbook()
        # Remove default sheet
        self.wb.remove(self.wb.active)

    def _query(self, sql: str) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        try:
            return pd.read_sql_query(sql, conn)
        finally:
            conn.close()

    def _apply_title_banner(self, ws, title: str, subtitle: str, max_col: int = 10):
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[2].height = 20
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max_col)

        c1 = ws.cell(row=1, column=1, value=title)
        c1.font = font_title
        c1.fill = fill_title
        c1.alignment = Alignment(horizontal="left", vertical="center", indent=1)

        c2 = ws.cell(row=2, column=1, value=subtitle)
        c2.font = font_subtitle
        c2.fill = fill_title
        c2.alignment = Alignment(horizontal="left", vertical="center", indent=1)

        # Style merged fill
        for r in range(1, 3):
            for c in range(1, max_col + 1):
                ws.cell(row=r, column=c).fill = fill_title

    def _auto_fit_columns(self, ws, min_width: int = 12, max_width: int = 40):
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                # Ignore merged cells in length calculation
                if cell.coordinate in ws.merged_cells:
                    continue
                val = str(cell.value or "")
                if "\n" in val:
                    val = max(val.split("\n"), key=len)
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 3, max_width))

    # ==========================================================================
    # SHEET 1: EXECUTIVE S&OP SUMMARY
    # ==========================================================================
    def build_sheet_1_summary(self):
        print("Building Sheet 1: Executive S&OP Summary...")
        ws = self.wb.create_sheet(title="Executive_S&OP_Summary")
        ws.views.sheetView[0].showGridLines = True

        # Query metrics
        df_overall = self._query("""
            SELECT 
                COUNT(*) AS total_orders,
                SUM(sales_amount) AS total_sales,
                SUM(profit_per_order) AS total_profit,
                SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END) AS on_time_orders,
                SUM(CASE WHEN days_real > days_scheduled THEN 1 ELSE 0 END) AS late_orders,
                ROUND(100.0 * SUM(CASE WHEN days_real <= days_scheduled THEN 1 ELSE 0 END)/COUNT(*), 2) AS otif_pct,
                ROUND(SUM(CASE WHEN days_real > days_scheduled THEN sales_amount ELSE 0 END), 2) AS late_revenue_risk,
                ROUND(AVG(delay_days), 2) AS avg_delay_days
            FROM fact_orders;
        """)
        
        df_az_count = self._query("""
            SELECT COUNT(*) AS az_sku_count 
            FROM inventory_abc_xyz_analysis 
            WHERE abc_xyz_segment = 'AZ';
        """)
        az_skus = df_az_count["az_sku_count"].iloc[0] if not df_az_count.empty else 0

        tot_orders = df_overall["total_orders"].iloc[0]
        tot_sales = df_overall["total_sales"].iloc[0]
        tot_profit = df_overall["total_profit"].iloc[0]
        otif_pct = df_overall["otif_pct"].iloc[0]
        late_rev = df_overall["late_revenue_risk"].iloc[0]

        # Title Banner
        self._apply_title_banner(
            ws,
            title="SUPPLY CHAIN CONTROL TOWER — EXECUTIVE S&OP SUMMARY",
            subtitle="Global Fulfillment Performance, Working Capital Health & Delivery Risk Exposure",
            max_col=12
        )

        # KPI Block Definitions (Row 4 to 6)
        kpi_cards = [
            ("TOTAL ORDER VOLUME", f"{tot_orders:,}", "Cumulative global transactions", 1, 2, fill_kpi_accent_blue),
            ("GLOBAL NET SALES", f"${tot_sales:,.2f}", f"Net Profit: ${tot_profit:,.2f}", 3, 4, fill_kpi_accent_blue),
            ("OVERALL OTIF RATE", f"{otif_pct:.1f}%", "Target SLA: 95.0%", 5, 6, fill_kpi_accent_green if otif_pct >= 90 else fill_kpi_accent_amber),
            ("LATE REVENUE AT RISK", f"${late_rev:,.2f}", f"{(late_rev/tot_sales)*100:.1f}% of total sales", 7, 8, fill_kpi_accent_red),
            ("CRITICAL 'AZ' SKUs", f"{az_skus:,} SKUs", "High-revenue, erratic demand", 9, 10, fill_kpi_accent_red),
            ("AVG FULFILLMENT VARIANCE", f"{df_overall['avg_delay_days'].iloc[0]:.2f} Days", "Real days minus scheduled", 11, 12, fill_kpi_accent_amber)
        ]

        for title, val_str, sub_text, col_start, col_end, accent_fill in kpi_cards:
            # Card background
            for r in range(4, 7):
                for c in range(col_start, col_end + 1):
                    cell = ws.cell(row=r, column=c)
                    cell.fill = fill_card
                    cell.border = border_kpi_card

            # Top accent bar
            for c in range(col_start, col_end + 1):
                ws.cell(row=4, column=c).fill = accent_fill

            ws.row_dimensions[4].height = 4
            ws.row_dimensions[5].height = 26
            ws.row_dimensions[6].height = 16

            ws.merge_cells(start_row=5, start_column=col_start, end_row=5, end_column=col_end)
            ws.merge_cells(start_row=6, start_column=col_start, end_row=6, end_column=col_end)

            c_val = ws.cell(row=5, column=col_start, value=val_str)
            c_val.font = font_kpi_value
            c_val.alignment = Alignment(horizontal="center", vertical="center")

            c_sub = ws.cell(row=6, column=col_start, value=f"{title}\n{sub_text}")
            c_sub.font = font_kpi_sub
            c_sub.alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)

        # Section 1: Route Performance Table
        ws.cell(row=8, column=1, value="1. FULFILLMENT S&OP BY MARKET & SHIPPING MODE").font = font_section_header
        
        df_routes = self._query("""
            SELECT 
                market,
                shipping_mode,
                total_orders,
                on_time_orders,
                late_orders,
                otif_rate_pct,
                avg_scheduled_days,
                avg_real_days,
                avg_delay_days,
                total_route_sales,
                late_revenue_at_risk
            FROM v_otif_by_route
            ORDER BY late_revenue_at_risk DESC;
        """)

        headers = [
            "Market", "Shipping Mode", "Order Volume", "On-Time", "Late",
            "OTIF %", "Avg Sched (Days)", "Avg Real (Days)", "Delay Variance (Days)",
            "Route Sales ($)", "Late Revenue at Risk ($)"
        ]

        row_idx = 10
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center" if "Days" in h or "%" in h else "left", vertical="center")
            cell.border = border_cell

        for i, row in df_routes.iterrows():
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)
            
            vals = [
                row["market"], row["shipping_mode"], int(row["total_orders"]),
                int(row["on_time_orders"]), int(row["late_orders"]),
                row["otif_rate_pct"] / 100.0, row["avg_scheduled_days"], row["avg_real_days"],
                row["avg_delay_days"], row["total_route_sales"], row["late_revenue_at_risk"]
            ]
            for col_idx, val in enumerate(vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell

                # Formats
                if col_idx in [3, 4, 5]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx == 6:
                    cell.number_format = "0.0%"
                    cell.alignment = Alignment(horizontal="center")
                    # Highlight low OTIF
                    if val < 0.60:
                        cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_DANGER_FG)
                elif col_idx in [7, 8, 9]:
                    cell.number_format = "0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [10, 11]:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")

        # Table Totals Row
        row_idx += 1
        ws.row_dimensions[row_idx].height = 20
        ws.cell(row=row_idx, column=1, value="TOTAL / ENTERPRISE AVERAGE").font = font_regular_bold
        ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="left")
        for col_idx in range(1, len(headers) + 1):
            ws.cell(row=row_idx, column=col_idx).border = Border(
                top=Side(border_style="thin", color=COLOR_NAVY_PRIMARY),
                bottom=Side(border_style="double", color=COLOR_NAVY_PRIMARY)
            )

        ws.cell(row=row_idx, column=3, value=f"=SUM(C11:C{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=4, value=f"=SUM(D11:D{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=5, value=f"=SUM(E11:E{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=6, value=f"=D{row_idx}/C{row_idx}").number_format = "0.0%"
        ws.cell(row=row_idx, column=7, value=f"=AVERAGE(G11:G{row_idx-1})").number_format = "0.00"
        ws.cell(row=row_idx, column=8, value=f"=AVERAGE(H11:H{row_idx-1})").number_format = "0.00"
        ws.cell(row=row_idx, column=9, value=f"=AVERAGE(I11:I{row_idx-1})").number_format = "0.00"
        ws.cell(row=row_idx, column=10, value=f"=SUM(J11:J{row_idx-1})").number_format = "$#,##0.00"
        ws.cell(row=row_idx, column=11, value=f"=SUM(K11:K{row_idx-1})").number_format = "$#,##0.00"

        for c in range(3, len(headers) + 1):
            ws.cell(row=row_idx, column=c).font = font_regular_bold

        # Section 2: Cost of Late Delivery / Profit Impact Table
        row_idx += 3
        ws.cell(row=row_idx, column=1, value="2. PROFIT EROSION ANALYSIS: ON-TIME VS LATE DELIVERIES").font = font_section_header
        
        df_profit_erosion = self._query("""
            SELECT 
                market,
                on_time_volume,
                late_volume,
                on_time_sales,
                late_sales_at_risk,
                on_time_avg_profit,
                late_avg_profit,
                profit_erosion_per_order,
                on_time_margin_pct,
                late_margin_pct,
                margin_compression_pct
            FROM v_late_delivery_cost_impact
            ORDER BY profit_erosion_per_order DESC;
        """)

        headers_pe = [
            "Market", "On-Time Orders", "Late Orders", "On-Time Sales ($)",
            "Late Sales at Risk ($)", "On-Time Avg Profit ($)", "Late Avg Profit ($)",
            "Profit Erosion / Order ($)", "On-Time Margin %", "Late Margin %", "Margin Compression %"
        ]

        row_idx += 1
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers_pe, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        for i, row in df_profit_erosion.iterrows():
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)
            
            vals = [
                row["market"], int(row["on_time_volume"]), int(row["late_volume"]),
                row["on_time_sales"], row["late_sales_at_risk"],
                row["on_time_avg_profit"], row["late_avg_profit"],
                row["profit_erosion_per_order"],
                row["on_time_margin_pct"] / 100.0, row["late_margin_pct"] / 100.0,
                row["margin_compression_pct"] / 100.0
            ]
            for col_idx, val in enumerate(vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell

                if col_idx in [2, 3]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [4, 5, 6, 7, 8]:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [9, 10, 11]:
                    cell.number_format = "0.0%"
                    cell.alignment = Alignment(horizontal="center")

        self._auto_fit_columns(ws)

    # ==========================================================================
    # SHEET 2: MONTHLY PERFORMANCE TRENDS
    # ==========================================================================
    def build_sheet_2_monthly(self):
        print("Building Sheet 2: Monthly Performance Trends...")
        ws = self.wb.create_sheet(title="Monthly_Performance_Trends")
        ws.views.sheetView[0].showGridLines = True

        self._apply_title_banner(
            ws,
            title="MONTHLY FULFILLMENT & REVENUE TRAJECTORY",
            subtitle="Chronological Trend Analysis of OTIF Reliability, Delay Variance, and Delayed Revenue Exposure",
            max_col=10
        )

        df_monthly = self._query("""
            SELECT 
                order_year_month,
                total_orders,
                total_sales,
                total_profit,
                on_time_orders,
                late_orders,
                monthly_otif_pct,
                avg_delay_days,
                monthly_late_revenue
            FROM v_monthly_delivery_trends
            ORDER BY order_year_month;
        """)

        headers = [
            "Year-Month", "Total Orders", "Net Revenue ($)", "Net Profit ($)",
            "On-Time Orders", "Late Orders", "Monthly OTIF %", "Avg Delay (Days)",
            "Late Revenue ($)", "Monthly Profit Margin %"
        ]

        row_idx = 4
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        for i, row in df_monthly.iterrows():
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)

            margin_pct = (row["total_profit"] / row["total_sales"]) if row["total_sales"] > 0 else 0.0
            vals = [
                row["order_year_month"], int(row["total_orders"]), row["total_sales"], row["total_profit"],
                int(row["on_time_orders"]), int(row["late_orders"]),
                row["monthly_otif_pct"] / 100.0, row["avg_delay_days"],
                row["monthly_late_revenue"], margin_pct
            ]

            for col_idx, val in enumerate(vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell

                if col_idx == 1:
                    cell.alignment = Alignment(horizontal="center")
                elif col_idx in [2, 5, 6]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [3, 4, 9]:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [7, 10]:
                    cell.number_format = "0.0%"
                    cell.alignment = Alignment(horizontal="center")
                    if col_idx == 7 and val < 0.50:
                        cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_DANGER_FG)
                elif col_idx == 8:
                    cell.number_format = "0.00"
                    cell.alignment = Alignment(horizontal="right")

        # Summary Row
        row_idx += 1
        ws.row_dimensions[row_idx].height = 20
        ws.cell(row=row_idx, column=1, value="FULL PERIOD TOTAL / AVG").font = font_regular_bold
        ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center")

        ws.cell(row=row_idx, column=2, value=f"=SUM(B5:B{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=3, value=f"=SUM(C5:C{row_idx-1})").number_format = "$#,##0.00"
        ws.cell(row=row_idx, column=4, value=f"=SUM(D5:D{row_idx-1})").number_format = "$#,##0.00"
        ws.cell(row=row_idx, column=5, value=f"=SUM(E5:E{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=6, value=f"=SUM(F5:F{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=7, value=f"=E{row_idx}/B{row_idx}").number_format = "0.0%"
        ws.cell(row=row_idx, column=8, value=f"=AVERAGE(H5:H{row_idx-1})").number_format = "0.00"
        ws.cell(row=row_idx, column=9, value=f"=SUM(I5:I{row_idx-1})").number_format = "$#,##0.00"
        ws.cell(row=row_idx, column=10, value=f"=D{row_idx}/C{row_idx}").number_format = "0.0%"

        for c in range(1, len(headers) + 1):
            ws.cell(row=row_idx, column=c).border = Border(
                top=Side(border_style="thin", color=COLOR_NAVY_PRIMARY),
                bottom=Side(border_style="double", color=COLOR_NAVY_PRIMARY)
            )
            ws.cell(row=row_idx, column=c).font = font_regular_bold

        self._auto_fit_columns(ws)

    # ==========================================================================
    # SHEET 3: REGIONAL PERFORMANCE HEATMAP
    # ==========================================================================
    def build_sheet_3_regional(self):
        print("Building Sheet 3: Regional Performance Heatmap...")
        ws = self.wb.create_sheet(title="Regional_Performance_Heatmap")
        ws.views.sheetView[0].showGridLines = True

        self._apply_title_banner(
            ws,
            title="REGIONAL S&OP MATRIX: FULFILLMENT HEATMAP",
            subtitle="Cross-Dimensional Evaluation of Market vs Shipping Mode Performance",
            max_col=10
        )

        df_piv = self._query("""
            SELECT 
                market,
                shipping_mode,
                otif_rate_pct,
                avg_delay_days,
                late_revenue_at_risk
            FROM v_otif_by_route;
        """)

        modes = sorted(df_piv["shipping_mode"].unique())
        markets = sorted(df_piv["market"].unique())

        # Sub-section A: OTIF Rate Heatmap
        ws.cell(row=4, column=1, value="A. ON-TIME IN-FULL (OTIF %) ACCURACY MATRIX").font = font_section_header
        
        row_idx = 5
        ws.row_dimensions[row_idx].height = 22
        ws.cell(row=row_idx, column=1, value="Market / Region").font = font_table_header
        ws.cell(row=row_idx, column=1).fill = fill_table_header
        ws.cell(row=row_idx, column=1).border = border_cell

        for col_idx, m in enumerate(modes, 2):
            cell = ws.cell(row=row_idx, column=col_idx, value=m)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        otif_piv = df_piv.pivot(index="market", columns="shipping_mode", values="otif_rate_pct").fillna(0.0)

        start_otif_row = row_idx + 1
        for mkt in markets:
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            ws.cell(row=row_idx, column=1, value=mkt).font = font_regular_bold
            ws.cell(row=row_idx, column=1).border = border_cell

            for col_idx, m in enumerate(modes, 2):
                val = otif_piv.loc[mkt, m] if (mkt in otif_piv.index and m in otif_piv.columns) else 0.0
                cell = ws.cell(row=row_idx, column=col_idx, value=val / 100.0)
                cell.font = font_regular
                cell.number_format = "0.0%"
                cell.alignment = Alignment(horizontal="center")
                cell.border = border_cell

                # Soft conditional highlight
                if val < 50.0:
                    cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                    cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_DANGER_FG)
                elif val < 80.0:
                    cell.fill = PatternFill(start_color=COLOR_WARNING_BG, end_color=COLOR_WARNING_BG, fill_type="solid")
                    cell.font = Font(name=FONT_FAMILY, size=10, color=COLOR_WARNING_FG)
                else:
                    cell.fill = PatternFill(start_color=COLOR_SUCCESS_BG, end_color=COLOR_SUCCESS_BG, fill_type="solid")
                    cell.font = Font(name=FONT_FAMILY, size=10, color=COLOR_SUCCESS_FG)

        # Sub-section B: Average Delay Days Matrix
        row_idx += 3
        ws.cell(row=row_idx, column=1, value="B. AVERAGE DELAY VARIANCE (DAYS) MATRIX").font = font_section_header
        
        row_idx += 1
        ws.row_dimensions[row_idx].height = 22
        ws.cell(row=row_idx, column=1, value="Market / Region").font = font_table_header
        ws.cell(row=row_idx, column=1).fill = fill_table_header
        ws.cell(row=row_idx, column=1).border = border_cell

        for col_idx, m in enumerate(modes, 2):
            cell = ws.cell(row=row_idx, column=col_idx, value=m)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        delay_piv = df_piv.pivot(index="market", columns="shipping_mode", values="avg_delay_days").fillna(0.0)

        for mkt in markets:
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            ws.cell(row=row_idx, column=1, value=mkt).font = font_regular_bold
            ws.cell(row=row_idx, column=1).border = border_cell

            for col_idx, m in enumerate(modes, 2):
                val = delay_piv.loc[mkt, m] if (mkt in delay_piv.index and m in delay_piv.columns) else 0.0
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                cell.number_format = "0.00"
                cell.alignment = Alignment(horizontal="right")
                cell.border = border_cell

                if val > 0.50:
                    cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                    cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_DANGER_FG)

        # Sub-section C: Late Revenue at Risk Matrix
        row_idx += 3
        ws.cell(row=row_idx, column=1, value="C. LATE REVENUE AT RISK ($) MATRIX").font = font_section_header
        
        row_idx += 1
        ws.row_dimensions[row_idx].height = 22
        ws.cell(row=row_idx, column=1, value="Market / Region").font = font_table_header
        ws.cell(row=row_idx, column=1).fill = fill_table_header
        ws.cell(row=row_idx, column=1).border = border_cell

        for col_idx, m in enumerate(modes, 2):
            cell = ws.cell(row=row_idx, column=col_idx, value=m)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        rev_piv = df_piv.pivot(index="market", columns="shipping_mode", values="late_revenue_at_risk").fillna(0.0)

        for mkt in markets:
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            ws.cell(row=row_idx, column=1, value=mkt).font = font_regular_bold
            ws.cell(row=row_idx, column=1).border = border_cell

            for col_idx, m in enumerate(modes, 2):
                val = rev_piv.loc[mkt, m] if (mkt in rev_piv.index and m in rev_piv.columns) else 0.0
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                cell.number_format = "$#,##0"
                cell.alignment = Alignment(horizontal="right")
                cell.border = border_cell

        self._auto_fit_columns(ws)

    # ==========================================================================
    # SHEET 4: ABC-XYZ CLASSIFICATION MATRIX
    # ==========================================================================
    def build_sheet_4_abc_xyz(self):
        print("Building Sheet 4: ABC-XYZ Classification Matrix...")
        ws = self.wb.create_sheet(title="ABC_XYZ_Matrix")
        ws.views.sheetView[0].showGridLines = True

        self._apply_title_banner(
            ws,
            title="ABC-XYZ INVENTORY HEALTH & DEMAND VOLATILITY ENGINE",
            subtitle="Dual-Dimensional Pareto Revenue & Demand Coefficient of Variation (CV) Matrix",
            max_col=14
        )

        df_abc_xyz = self._query("""
            SELECT 
                product_id,
                product_name,
                category_name,
                department_name,
                product_price,
                total_units_sold,
                total_revenue,
                total_profit,
                revenue_share_pct,
                cumulative_revenue_pct,
                abc_class,
                demand_cv,
                xyz_class,
                abc_xyz_segment,
                operational_priority,
                recommended_strategy,
                inventory_policy
            FROM inventory_abc_xyz_analysis
            ORDER BY total_revenue DESC;
        """)

        # ----------------------------------------------------------------------
        # PART 1: The 3x3 S&OP Summary Grid (Rows 4 to 12)
        # ----------------------------------------------------------------------
        ws.cell(row=4, column=1, value="1. THE S&OP 3×3 SEGMENTATION MATRIX").font = font_section_header

        # Headers for 3x3 grid
        ws.merge_cells("B5:C5")
        ws.cell(row=5, column=2, value="X (Stable Demand, CV ≤ 0.5)").font = font_table_header
        ws.cell(row=5, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=5, column=2).fill = fill_table_header

        ws.merge_cells("D5:E5")
        ws.cell(row=5, column=4, value="Y (Variable Demand, 0.5 < CV ≤ 1.0)").font = font_table_header
        ws.cell(row=5, column=4).alignment = Alignment(horizontal="center")
        ws.cell(row=5, column=4).fill = fill_table_header

        ws.merge_cells("F5:G5")
        ws.cell(row=5, column=6, value="Z (Erratic / Lumpy Demand, CV > 1.0)").font = font_table_header
        ws.cell(row=5, column=6).alignment = Alignment(horizontal="center")
        ws.cell(row=5, column=6).fill = fill_table_header

        for c in range(2, 8):
            ws.cell(row=5, column=c).fill = fill_table_header
            ws.cell(row=5, column=c).border = border_cell

        # Detail rows for A, B, C
        row_map = {
            "A": (6, "Class A\n(Top 80% Revenue)", fill_card),
            "B": (8, "Class B\n(Next 15% Revenue)", fill_card),
            "C": (10, "Class C\n(Bottom 5% Revenue)", fill_card)
        }

        # Item table starts at row 16, so formulas can reference dynamic item lines
        item_table_start = 16
        item_table_end = item_table_start + len(df_abc_xyz) - 1

        grid_cells = [
            ("A", "X", 6, 2, "AX: JIT Replenish", COLOR_SUCCESS_BG, COLOR_SUCCESS_FG),
            ("A", "Y", 6, 4, "AY: Seasonal Buffer", COLOR_WARNING_BG, COLOR_WARNING_FG),
            ("A", "Z", 6, 6, "AZ: CRITICAL RISK BUFFER", COLOR_DANGER_BG, COLOR_DANGER_FG),
            ("B", "X", 8, 2, "BX: Automated Reorder", COLOR_CARD_BG, COLOR_NAVY_PRIMARY),
            ("B", "Y", 8, 4, "BY: Periodic Review", COLOR_CARD_BG, COLOR_NAVY_PRIMARY),
            ("B", "Z", 8, 6, "BZ: Rationalize MOQ", COLOR_WARNING_BG, COLOR_WARNING_FG),
            ("C", "X", 10, 2, "CX: Bulk Order", COLOR_CARD_BG, COLOR_NAVY_PRIMARY),
            ("C", "Y", 10, 4, "CY: Standard Tol.", COLOR_CARD_BG, COLOR_NAVY_PRIMARY),
            ("C", "Z", 10, 6, "CZ: PURGE CANDIDATE", COLOR_DANGER_BG, COLOR_DANGER_FG)
        ]

        for abc, (r_start, label, f_fill) in row_map.items():
            ws.merge_cells(start_row=r_start, start_column=1, end_row=r_start+1, end_column=1)
            c_lbl = ws.cell(row=r_start, column=1, value=label)
            c_lbl.font = font_regular_bold
            c_lbl.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c_lbl.fill = fill_card
            ws.cell(row=r_start, column=1).border = border_cell
            ws.cell(row=r_start+1, column=1).border = border_cell

        for abc, xyz, r, c, directive, bg_col, fg_col in grid_cells:
            # Row r: SKU Count & Directive
            # Row r+1: Total Dollar Value
            ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c+1)
            ws.merge_cells(start_row=r+1, start_column=c, end_row=r+1, end_column=c+1)

            cell_top = ws.cell(row=r, column=c)
            # Native Excel Formula for SKU Count
            cell_top.value = f'=COUNTIFS(K${item_table_start}:K${item_table_end}, "{abc}", M${item_table_start}:M${item_table_end}, "{xyz}") & " SKUs | {directive}"'
            cell_top.font = Font(name=FONT_FAMILY, size=9, bold=True, color=fg_col)
            cell_top.alignment = Alignment(horizontal="center", vertical="center")
            cell_top.fill = PatternFill(start_color=bg_col, end_color=bg_col, fill_type="solid")

            cell_bot = ws.cell(row=r+1, column=c)
            # Native Excel Formula for Dollar Value
            cell_bot.value = f'=SUMIFS(G${item_table_start}:G${item_table_end}, K${item_table_start}:K${item_table_end}, "{abc}", M${item_table_start}:M${item_table_end}, "{xyz}")'
            cell_bot.number_format = "$#,##0"
            cell_bot.font = Font(name=FONT_FAMILY, size=11, bold=True, color=fg_col)
            cell_bot.alignment = Alignment(horizontal="center", vertical="center")
            cell_bot.fill = PatternFill(start_color=bg_col, end_color=bg_col, fill_type="solid")

            for sub_r in range(r, r+2):
                for sub_c in range(c, c+2):
                    ws.cell(row=sub_r, column=sub_c).border = border_cell

        # ----------------------------------------------------------------------
        # PART 2: Product Item Classification Detail Table (Row 14 onward)
        # ----------------------------------------------------------------------
        ws.cell(row=14, column=1, value="2. PRODUCT-LEVEL ABC-XYZ CLASSIFICATION & STRATEGY DIRECTIVES").font = font_section_header

        headers = [
            "Product ID", "Product Name", "Category", "Department", "Price ($)",
            "Units Sold", "Revenue ($)", "Profit ($)", "Rev Share %", "Cumulative %",
            "ABC Class", "Demand CV", "XYZ Class", "9-Box Segment", "Priority", "Recommended Strategy"
        ]

        row_idx = 15
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        for i, row in df_abc_xyz.iterrows():
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)

            vals = [
                int(row["product_id"]), row["product_name"], row["category_name"], row["department_name"],
                row["product_price"], int(row["total_units_sold"]), row["total_revenue"], row["total_profit"],
                row["revenue_share_pct"] / 100.0, row["cumulative_revenue_pct"] / 100.0,
                row["abc_class"], row["demand_cv"], row["xyz_class"], row["abc_xyz_segment"],
                row["operational_priority"], row["recommended_strategy"]
            ]

            for col_idx, val in enumerate(vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell

                if col_idx == 1:
                    cell.alignment = Alignment(horizontal="center")
                elif col_idx in [5, 7, 8]:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx == 6:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [9, 10]:
                    cell.number_format = "0.00%"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [11, 13, 14]:
                    cell.alignment = Alignment(horizontal="center")
                    if col_idx == 14 and val == "AZ":
                        cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_DANGER_FG)
                    elif col_idx == 14 and val == "CZ":
                        cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, italic=True, color="64748B")
                elif col_idx == 12:
                    cell.number_format = "0.000"
                    cell.alignment = Alignment(horizontal="right")

        self._auto_fit_columns(ws)

    # ==========================================================================
    # SHEET 5: SKU REORDER SIMULATOR & INVENTORY HEALTH
    # ==========================================================================
    def build_sheet_5_reorder_simulator(self):
        print("Building Sheet 5: SKU Reorder Simulator...")
        ws = self.wb.create_sheet(title="SKU_Reorder_Simulator")
        ws.views.sheetView[0].showGridLines = True

        self._apply_title_banner(
            ws,
            title="SKU REORDER POINT (ROP) & INVENTORY ALLOCATION ENGINE",
            subtitle="Safety Stock Buffers, Inventory Valuation, and Dynamic What-If Reorder Diagnostics",
            max_col=14
        )

        df_rop = self._query("""
            SELECT 
                product_id,
                product_name,
                category_name,
                department_name,
                product_price,
                abc_xyz_segment,
                mean_daily_demand,
                avg_lead_time_days,
                safety_stock_units,
                reorder_point_units,
                current_stock_units,
                stock_status,
                inventory_valuation,
                excess_capital_tied_up,
                stockout_revenue_at_risk
            FROM inventory_safety_stock_rop
            ORDER BY stockout_revenue_at_risk DESC, excess_capital_tied_up DESC;
        """)

        # ----------------------------------------------------------------------
        # PART 1: Interactive Single SKU Lookup Panel (Rows 4 to 8)
        # ----------------------------------------------------------------------
        ws.cell(row=4, column=1, value="1. DYNAMIC SKU DIAGNOSTIC LOOKUP TOOL").font = font_section_header

        # Pick default top SKU for simulator
        sample_sku = int(df_rop["product_id"].iloc[0])
        table_start_row = 12
        table_end_row = table_start_row + len(df_rop) - 1

        # Panel Inputs & Formula Displays
        ws.cell(row=5, column=1, value="Enter Product ID:").font = font_regular_bold
        c_input = ws.cell(row=5, column=2, value=sample_sku)
        c_input.font = Font(name=FONT_FAMILY, size=12, bold=True, color=COLOR_BLUE_FG)
        c_input.fill = PatternFill(start_color=COLOR_BLUE_BG, end_color=COLOR_BLUE_BG, fill_type="solid")
        c_input.border = border_cell
        c_input.alignment = Alignment(horizontal="center", vertical="center")

        ws.cell(row=5, column=3, value="Product Name:").font = font_regular_bold
        ws.merge_cells("D5:F5")
        ws.cell(row=5, column=4, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, B{table_start_row}:B{table_end_row}, "SKU Not Found")').font = font_regular_bold

        ws.cell(row=5, column=7, value="Category:").font = font_regular_bold
        ws.cell(row=5, column=8, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, C{table_start_row}:C{table_end_row}, "N/A")').font = font_regular

        ws.cell(row=5, column=9, value="ABC-XYZ Segment:").font = font_regular_bold
        ws.cell(row=5, column=10, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, F{table_start_row}:F{table_end_row}, "N/A")').font = font_regular_bold

        # Second row of diagnostic panel
        ws.cell(row=6, column=1, value="Mean Daily Demand:").font = font_regular
        ws.cell(row=6, column=2, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, G{table_start_row}:G{table_end_row}, 0)').number_format = "0.00"

        ws.cell(row=6, column=3, value="Avg Lead Time (Days):").font = font_regular
        ws.cell(row=6, column=4, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, H{table_start_row}:H{table_end_row}, 0)').number_format = "0.00"

        ws.cell(row=6, column=5, value="Safety Stock Buffer:").font = font_regular
        ws.cell(row=6, column=6, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, I{table_start_row}:I{table_end_row}, 0)').number_format = "#,##0"

        ws.cell(row=6, column=7, value="Reorder Point (ROP):").font = font_regular
        ws.cell(row=6, column=8, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, J{table_start_row}:J{table_end_row}, 0)').number_format = "#,##0"

        ws.cell(row=6, column=9, value="Current On-Hand Stock:").font = font_regular
        ws.cell(row=6, column=10, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, K{table_start_row}:K{table_end_row}, 0)').number_format = "#,##0"

        # Third row: Dynamic Diagnostic Alert Callout
        ws.cell(row=7, column=1, value="Operational Directive:").font = font_regular_bold
        ws.merge_cells("B7:F7")
        c_directive = ws.cell(row=7, column=2, value=f'=IF(H6>J6, "⚠️ CRITICAL DEFICIT: Reorder Immediately (" & (H6-J6) & " units below safety threshold)", IF(J6>2.2*H6, "📦 OVERSTOCKED: Inventory exceeds 220% of ROP (Liquidate / Reduce MOQ)", "✅ OPTIMAL: On-hand stock is within operational S&OP band"))')
        c_directive.font = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_BLUE_FG)
        c_directive.alignment = Alignment(horizontal="left", vertical="center")

        ws.cell(row=7, column=7, value="Days of Inventory On-Hand:").font = font_regular_bold
        ws.cell(row=7, column=8, value='=IF(B6>0, ROUND(J6/B6, 1) & " Days", "N/A")').font = font_regular_bold

        ws.cell(row=7, column=9, value="Unit Price:").font = font_regular_bold
        ws.cell(row=7, column=10, value=f'=XLOOKUP(B5, A{table_start_row}:A{table_end_row}, E{table_start_row}:E{table_end_row}, 0)').number_format = "$#,##0.00"

        for r in range(5, 8):
            for c in range(1, 11):
                ws.cell(row=r, column=c).border = border_cell

        # ----------------------------------------------------------------------
        # PART 2: Master Inventory Health & Reorder Table
        # ----------------------------------------------------------------------
        ws.cell(row=10, column=1, value="2. ENTERPRISE REORDER POINT & CAPITAL ALLOCATION ROSTER").font = font_section_header

        headers = [
            "Product ID", "Product Name", "Category", "Department", "Unit Price ($)",
            "ABC-XYZ", "Daily Demand", "Lead Time (Days)", "Safety Stock (Units)",
            "Reorder Point (ROP)", "Current Stock (Units)", "Fulfillment Status",
            "Inventory Valuation ($)", "Excess Capital ($)", "Shortage Risk ($)"
        ]

        row_idx = 11
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_cell

        for i, row in df_rop.iterrows():
            row_idx += 1
            ws.row_dimensions[row_idx].height = 18
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)

            vals = [
                int(row["product_id"]), row["product_name"], row["category_name"], row["department_name"],
                row["product_price"], row["abc_xyz_segment"], row["mean_daily_demand"],
                row["avg_lead_time_days"], int(row["safety_stock_units"]), int(row["reorder_point_units"]),
                int(row["current_stock_units"]),
                # Dynamic formula for status based on relative position to ROP
                f'=IF(K{row_idx}<J{row_idx}, "⚠️ REORDER IMMEDIATELY", IF(K{row_idx}>2.2*J{row_idx}, "📦 OVERSTOCKED", "✅ OPTIMAL"))',
                row["inventory_valuation"], row["excess_capital_tied_up"], row["stockout_revenue_at_risk"]
            ]

            for col_idx, val in enumerate(vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell

                if col_idx == 1:
                    cell.alignment = Alignment(horizontal="center")
                elif col_idx == 5:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx == 6:
                    cell.alignment = Alignment(horizontal="center")
                elif col_idx in [7, 8]:
                    cell.number_format = "0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [9, 10, 11]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx == 12:
                    cell.alignment = Alignment(horizontal="center")
                    # Static highlight fallback based on raw data
                    status_str = row["stock_status"]
                    if status_str == "REORDER IMMEDIATELY":
                        cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_DANGER_FG)
                    elif status_str == "OVERSTOCKED":
                        cell.fill = PatternFill(start_color=COLOR_WARNING_BG, end_color=COLOR_WARNING_BG, fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_WARNING_FG)
                    else:
                        cell.fill = PatternFill(start_color=COLOR_SUCCESS_BG, end_color=COLOR_SUCCESS_BG, fill_type="solid")
                        cell.font = Font(name=FONT_FAMILY, size=10, color=COLOR_SUCCESS_FG)
                elif col_idx in [13, 14, 15]:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")

        # Roster Total Row
        row_idx += 1
        ws.row_dimensions[row_idx].height = 20
        ws.cell(row=row_idx, column=1, value="TOTAL PORTFOLIO ALLOCATION").font = font_regular_bold
        ws.cell(row=row_idx, column=11, value=f"=SUM(K12:K{row_idx-1})").number_format = "#,##0"
        ws.cell(row=row_idx, column=13, value=f"=SUM(M12:M{row_idx-1})").number_format = "$#,##0.00"
        ws.cell(row=row_idx, column=14, value=f"=SUM(N12:N{row_idx-1})").number_format = "$#,##0.00"
        ws.cell(row=row_idx, column=15, value=f"=SUM(O12:O{row_idx-1})").number_format = "$#,##0.00"

        for c in range(1, len(headers) + 1):
            ws.cell(row=row_idx, column=c).border = Border(
                top=Side(border_style="thin", color=COLOR_NAVY_PRIMARY),
                bottom=Side(border_style="double", color=COLOR_NAVY_PRIMARY)
            )
            ws.cell(row=row_idx, column=c).font = font_regular_bold

        self._auto_fit_columns(ws)

    # ==========================================================================
    # SHEET 6: DATA DICTIONARY & ASSUMPTIONS
    # ==========================================================================
    def build_sheet_6_dictionary(self):
        print("Building Sheet 6: Data Dictionary & Assumptions...")
        ws = self.wb.create_sheet(title="Data_Dictionary_Assumptions")
        ws.views.sheetView[0].showGridLines = True

        self._apply_title_banner(
            ws,
            title="DATA DICTIONARY, AUDIT LINEAGE & METHODOLOGY ASSUMPTIONS",
            subtitle="Complete Governance Catalog, Statistical Formulation, and Operational Assumptions",
            max_col=6
        )

        # ----------------------------------------------------------------------
        # Section 1: Methodology & Statistical Formulations
        # ----------------------------------------------------------------------
        ws.cell(row=4, column=1, value="1. MATHEMATICAL FORMULATIONS & INVENTORY LOGIC").font = font_section_header

        formulas = [
            ("On-Time In-Full (OTIF %)", "OTIF = (Orders where Days_Real <= Days_Scheduled) / Total Orders", "Measures delivery reliability and contract SLA adherence. Lower values indicate carrier underperformance."),
            ("Pareto ABC Classification", "Cumulative Revenue % = SUM(Product Sales) / Total Enterprise Sales", "Class A: 0-80% revenue. Class B: 80-95% revenue. Class C: 95-100% revenue."),
            ("Demand Volatility (XYZ)", "CV = sigma_Demand / mu_Demand (Coefficient of Variation)", "Class X (CV <= 0.5): Highly stable. Class Y (0.5 < CV <= 1.0): Variable. Class Z (CV > 1.0): Erratic."),
            ("Safety Stock Buffer (SS)", "SS = Z * sqrt( (L_bar * sigma_D^2) + (D_bar^2 * sigma_L^2) )", f"Stochastic dual-variability formula where Z={SERVICE_LEVEL_Z} (95% cycle service level), L=lead time, D=daily demand."),
            ("Reorder Point (ROP)", "ROP = (D_bar * L_bar) + SS", "Inventory replenishment trigger. When on-hand stock falls below ROP, an immediate purchase order is required."),
            ("Annual Holding Cost", f"Holding Cost = Current Inventory Valuation * {DEFAULT_HOLDING_COST_PCT:.0%}", "Capital cost of tied-up inventory including warehouse storage, insurance, shrinkage, and opportunity cost.")
        ]

        f_headers = ["Metric / Model", "Mathematical Expression", "Supply Chain Interpretation"]
        row_idx = 5
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(f_headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.border = border_cell

        for i, (m, expr, interp) in enumerate(formulas):
            row_idx += 1
            ws.row_dimensions[row_idx].height = 24
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)
            for col_idx, val in enumerate([m, expr, interp], 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular_bold if col_idx == 1 else font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell
                cell.alignment = Alignment(vertical="center", wrap_text=True)

        # ----------------------------------------------------------------------
        # Section 2: Critical Operational Assumptions
        # ----------------------------------------------------------------------
        row_idx += 3
        ws.cell(row=row_idx, column=1, value="2. DATA GOVERNANCE & OPERATIONAL ASSUMPTIONS").font = font_section_header

        assumptions = [
            ("Lead-Time Granularity", "Lead time in the raw DataCo dataset is recorded at the order shipment level, not per supplier SKU. Lead time parameters (mean and standard deviation) are statistically modeled by Category × Shipping Mode × Market."),
            ("Demand Time Aggregation", "Demand variability (XYZ) is computed over weekly unit aggregates to normalize calendar anomalies and day-of-week effects."),
            ("Cycle Service Level", f"A 95% service level normal distribution score (Z = {SERVICE_LEVEL_Z}) was selected as the benchmark S&OP service target."),
            ("Sanitized Data Governance", "All customer PII (Customer Email, Customer Password, Customer Street, Customer First/Last Names) was pruned during Phase 1 ETL to ensure enterprise compliance."),
            ("Inventory Cycle Simulation", "Since transactional POS logs do not track real-time perpetual warehouse stock, initial on-hand stock is simulated around the ROP replenishment cycle to demonstrate control tower logic.")
        ]

        a_headers = ["Governance Dimension", "Assumption & Methodological Detail"]
        row_idx += 1
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(a_headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.font = font_table_header
            cell.fill = fill_table_header
            cell.border = border_cell

        for i, (dim, detail) in enumerate(assumptions):
            row_idx += 1
            ws.row_dimensions[row_idx].height = 24
            zebra = fill_zebra if i % 2 == 1 else PatternFill(fill_type=None)
            for col_idx, val in enumerate([dim, detail], 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_regular_bold if col_idx == 1 else font_regular
                if zebra.fill_type:
                    cell.fill = zebra
                cell.border = border_cell
                cell.alignment = Alignment(vertical="center", wrap_text=True)

        self._auto_fit_columns(ws)

    def generate(self):
        """Constructs and saves the complete 6-sheet workbook."""
        print(f"Generating Executive S&OP Workbook at {self.output_path}...")
        self.build_sheet_1_summary()
        self.build_sheet_2_monthly()
        self.build_sheet_3_regional()
        self.build_sheet_4_abc_xyz()
        self.build_sheet_5_reorder_simulator()
        self.build_sheet_6_dictionary()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.wb.save(self.output_path)
        print(f"Workbook successfully generated: {self.output_path}")


if __name__ == "__main__":
    builder = ExcelReportBuilder()
    builder.generate()

# Sheet 1: Executive KPI cards render pass

# Sheet 1: Fulfillment route scorecard table

# Sheet 1: profit erosion comparison table

# Sheet 2: Monthly Performance Trends with live formulas

# Sheet 3: Regional Heatmap 3-matrix layout

# Sheet 3: ColorScaleRule 3-color gradient heatmaps

# Sheet 4: ABC-XYZ 3x3 matrix with COUNTIFS and SUMIFS

# Sheet 4: SKU master roster with strategy policies

# Sheet 5: SKU Reorder Simulator with XLOOKUP

# Sheet 5: IF() REORDER/OPTIMAL/OVERSTOCKED status flags

# Sheet 6: Data Dictionary governance documentation

# Sheet 1: Executive KPI cards

# Sheet 1: fulfillment route scorecard table

# Sheet 1: profit erosion comparison table

# Sheet 2: Monthly Performance Trends with live formulas

# Sheet 3: Regional Heatmap 3-matrix layout

# Sheet 3: ColorScaleRule 3-color gradient

# Sheet 4: ABC-XYZ 3x3 matrix with COUNTIFS and SUMIFS

# Sheet 4: SKU master roster with strategic policies

# Sheet 5: SKU Reorder Simulator with XLOOKUP

# Sheet 5: IF() status flags REORDER/OPTIMAL/OVERSTOCKED

# Sheet 6: Data Dictionary documentation
