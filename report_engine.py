
from fpdf import FPDF
from datetime import datetime
import pandas as pd

class PDFReport(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Kairos Financial OS // Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)

    def cover_page(self, username, net_worth):
        self.add_page()
        # Logo/Brand
        self.set_font('Arial', 'B', 24)
        self.set_text_color(0, 0, 0) # Black
        self.ln(60)
        self.cell(0, 10, "KAIROS", 0, 1, 'C')
        self.set_font('Arial', 'B', 30)
        self.set_text_color(0, 150, 255) # Cyan-ish
        self.cell(0, 15, "INTELLIGENCE REPORT", 0, 1, 'C')
        
        self.ln(20)
        self.set_font('Arial', '', 12)
        self.set_text_color(100)
        self.cell(0, 10, f"Prepared for Operator: {username}", 0, 1, 'C')
        self.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", 0, 1, 'C')
        
        self.ln(30)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0)
        self.cell(0, 10, "CURRENT NET WORTH", 0, 1, 'C')
        self.set_font('Arial', 'B', 40)
        self.cell(0, 20, f"EUR {net_worth:,.2f}", 0, 1, 'C')

    def financial_page(self, metrics, df_c, df_a, df_l):
        self.add_page()
        self.chapter_title("1. FINANCIAL OVERVIEW")
        
        # --- INCOME STATEMENT (Mini) ---
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "INCOME STATEMENT (Monthly Average)", 0, 1)
        
        self.set_font('Arial', '', 10)
        # Calculate totals from metrics or df
        inc = 0
        exp = 0
        if not df_c.empty:
            # Re-calculate to be sure or use metrics passed? 
            # metrics['cashflow'] is net. We need gross.
            # Let's recalculate simply here to be safe and independent
            calc_df = df_c.copy()
            calc_df['m'] = calc_df.apply(lambda x: x['amount']/12 if x['frequency']=='Yearly' else x['amount'], axis=1)
            inc = calc_df[calc_df['type']=='Income']['m'].sum()
            exp = calc_df[calc_df['type']=='Expense']['m'].sum()
            
        self.set_fill_color(240, 240, 240)
        self.cell(100, 8, "Total Monthly Income", 1, 0, 'L', 1)
        self.cell(50, 8, f"EUR {inc:,.2f}", 1, 1, 'R')
        self.cell(100, 8, "Total Monthly Expenses", 1, 0, 'L', 1)
        self.cell(50, 8, f"EUR {exp:,.2f}", 1, 1, 'R')
        
        self.set_font('Arial', 'B', 10)
        self.cell(100, 8, "NET CASHFLOW", 1, 0, 'L', 1)
        if (inc - exp) >= 0:
            self.set_text_color(0, 150, 0)
        else:
             self.set_text_color(200, 0, 0)
        self.cell(50, 8, f"EUR {inc-exp:,.2f}", 1, 1, 'R')
        self.set_text_color(0)
        
        self.ln(10)
        
        # --- BALANCE SHEET ---
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "BALANCE SHEET", 0, 1)
        
        # Assets by Category
        self.set_font('Arial', 'B', 10)
        self.cell(100, 8, "ASSETS", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10)
        
        total_a = 0
        if not df_a.empty:
            # Group by category
            if 'current_price' in df_a.columns:
                 df_a['val'] = df_a['quantity'] * df_a['current_price']
                 cats = df_a.groupby('category')['val'].sum()
                 for cat, val in cats.items():
                     self.cell(100, 8, f"  - {cat}", 1, 0)
                     self.cell(50, 8, f"{val:,.2f}", 1, 1, 'R')
                     total_a += val
        
        self.set_font('Arial', 'B', 10)
        self.cell(100, 8, "TOTAL ASSETS", 1, 0)
        self.cell(50, 8, f"EUR {total_a:,.2f}", 1, 1, 'R')
        
        self.ln(5)
        
        # Liabilities
        self.cell(100, 8, "LIABILITIES", 1, 1, 'L', 1)
        self.set_font('Arial', '', 10)
        total_l = metrics['liabilities']
        self.cell(100, 8, "  - Total Debt Load", 1, 0)
        self.cell(50, 8, f"EUR {total_l:,.2f}", 1, 1, 'R')
        
        self.ln(5)
        
        # Equity
        self.set_font('Arial', 'B', 10)
        self.cell(100, 8, "TOTAL EQUITY (Net Worth)", 1, 0, 'L', 1)
        self.cell(50, 8, f"EUR {total_a - total_l:,.2f}", 1, 1, 'R')

    def strategy_page(self, freedom_index):
        self.add_page()
        self.chapter_title("2. STRATEGIC INSIGHT (THE ORACLE)")
        
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f"FREEDOM INDEX SCORE: {freedom_index:.1f}%", 0, 1)
        self.ln(5)
        
        # Oracle Logic
        msg = ""
        color = (0, 0, 0)
        if freedom_index < 20:
             msg = "WARNING: HIGH RELIANCE ON ACTIVE INCOME.\nTarget: Increase passive cashflow streams immediately. Reduce liabilities."
             color = (200, 0, 0)
        elif freedom_index < 50:
             msg = "STATUS: BUILDING MOMENTUM.\n\nYou are on the right track but still dependent on your job.\nFocus on acquiring income-generating assets."
             color = (200, 100, 0) # Orange
        elif freedom_index < 100:
             msg = "STATUS: RAT RACE ESCAPE IMMINENT.\n\nYou are over halfway there. Accelerate asset accumulation."
             color = (0, 150, 0)
        else:
             msg = "STATUS: FINANCIALLY FREE.\n\nCongratulations. You have escaped the Rat Race."
             color = (0, 200, 0)
             
        self.set_font('Courier', 'B', 12)
        self.set_text_color(*color)
        self.multi_cell(0, 10, msg, 1)
        self.set_text_color(0)
        
        self.ln(20)
        self.set_font('Arial', 'I', 10)
        self.multi_cell(0, 10, "This report was generated by Kairos Financial OS. \nDecisions should be based on professional financial advice.")

def generate_report(user_id, username, metrics, df_a, df_l, df_c):
    pdf = PDFReport()
    pdf.cover_page(username, metrics['net_worth'])
    pdf.financial_page(metrics, df_c, df_a, df_l)
    pdf.strategy_page(metrics['freedom_index'])
    
    try:
        return pdf.output(dest='S').encode('latin-1')
    except:
        return pdf.output(dest='S').encode('latin-1', errors='replace')
