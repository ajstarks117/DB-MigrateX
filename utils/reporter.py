# utils/reporter.py
from fpdf import FPDF
import json
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DB-MigrateX: Execution Audit Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(json_path="forensic_report.json", output_path="Final_Audit_Report.pdf"):
    if not os.path.exists(json_path):
        print("Warning: No forensic report found. Skipping PDF generation.")
        return

    # 1. Load Data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 2. Executive Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Executive Summary", 0, 1)
    pdf.set_font("Arial", size=12)
    
    start_time = data.get("start_time", "N/A")
    pdf.cell(0, 10, f"Execution Date: {start_time}", 0, 1)
    
    err_count = len(data.get("errors", []))
    status = "SUCCESS" if err_count == 0 else "COMPLETED WITH ERRORS"
    
    # Set color: Green (0,128,0) or Red (255,0,0)
    if err_count == 0:
        pdf.set_text_color(0, 128, 0)
    else:
        pdf.set_text_color(255, 0, 0)
        
    pdf.cell(0, 10, f"Status: {status}", 0, 1)
    pdf.set_text_color(0, 0, 0) # Reset to black
    pdf.ln(5)

    # 3. Migration Statistics
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Migration Statistics (Rows Processed)", 0, 1)
    pdf.set_font("Arial", size=12)

    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 10, "Table Name", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Rows", 1, 0, 'C', 1)
    pdf.cell(60, 10, "Status", 1, 1, 'C', 1)

    # Table Rows
    mig_stats = data.get("migration_stats", {})
    for table, info in mig_stats.items():
        # Clean data before writing to PDF
        status_text = str(info.get("status", "OK")).replace("✅", "[OK]") 
        
        pdf.cell(60, 10, str(table), 1)
        pdf.cell(40, 10, str(info.get("rows", 0)), 1)
        pdf.cell(60, 10, status_text, 1, 1)
    
    pdf.ln(10)

    # 4. Data Quality Issues
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "3. Data Quality Issues Detected", 0, 1)
    pdf.set_font("Arial", size=12)

    issues = data.get("data_quality_issues", [])
    if not issues:
        pdf.set_text_color(0, 128, 0)
        # --- FIX: Removed Emoji ---
        pdf.cell(0, 10, "[PASS] No data quality issues found.", 0, 1)
        pdf.set_text_color(0, 0, 0)
    else:
        pdf.set_text_color(255, 0, 0)
        for issue in issues:
            text = f"[{issue['table'].upper()}] {issue['type']}: {issue['details']}"
            # Ensure no unicode chars slip through
            clean_text = text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
        pdf.set_text_color(0, 0, 0)

    # 5. Output
    try:
        pdf.output(output_path)
        print(f"📄 PDF Report generated: {output_path}")
    except Exception as e:
        print(f"⚠️ Failed to save PDF: {e}")

if __name__ == "__main__":
    generate_pdf_report()