import streamlit as st
import pandas as pd
from database import init_db, get_clients, add_client, delete_client, update_client
from datetime import date
from fpdf import FPDF
import sqlite3
import json
init_db()
st.set_page_config(page_title="Audit Client Tracker", layout="wide")
# --- HELPER FOR PERFECT RECTANGLE TABLES ---
def draw_rect_row(pdf, label, value, label_w=65, value_w=125, h=8):
    """Draws a table row where both cells have the same height even with text wrapping."""
    curr_x = pdf.get_x()
    curr_y = pdf.get_y()
    
    # Check for page break
    if curr_y > 260:
        pdf.add_page()
        curr_y = pdf.get_y()

    # 1. Calculate height for the Right Value first (it's usually longer)
    pdf.set_font("Arial", '', 9)
    # We use multi_cell with split_only=True to calculate height without drawing
    # In standard FPDF, we calculate lines manually:
    lines = pdf.multi_cell(value_w, h, f" {value}", border=0, split_only=True)
    val_height = len(lines) * h
    
    # 2. Determine final row height (at least 'h')
    row_height = max(h, val_height)
    
    # 3. Draw Left Label
    pdf.set_font("Arial", 'B', 9)
    pdf.set_xy(curr_x, curr_y)
    pdf.multi_cell(label_w, row_height, f" {label}", border=1)
    
    # 4. Draw Right Value
    pdf.set_xy(curr_x + label_w, curr_y)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(value_w, h, f" {value}", border=1)
    
    # 5. Reset position for next row
    pdf.set_xy(curr_x, curr_y + row_height)
def load_client_data(client_name):
    conn = sqlite3.connect('clients_kyc.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kyc_records 
                 (client_name TEXT PRIMARY KEY, data_json TEXT)''')
    c.execute("SELECT data_json FROM kyc_records WHERE client_name=?", (client_name,))
    row = c.fetchone()
    conn.close()
    
    if row:
        data = json.loads(row[0])
        for key, value in data.items():
            # CRITICAL FIX: Skip keys used for buttons or navigation
            # These are the ones causing the "AssignmentNotAllowedError"
            if any(x in key for x in ["btn", "next", "back", "submit", "loaded"]):
                continue
            
            if key.startswith("__") or key.startswith("emp_cv_"):
                continue
            
            # Handling Dates
            if 'date' in key or 'dob' in key:
                try:
                    if isinstance(value, str) and value:
                        st.session_state[key] = date.fromisoformat(value)
                except:
                    st.session_state[key] = value
            else:
                # Use the 'set' method or simple assignment ONLY if key isn't a widget already
                try:
                    st.session_state[key] = value
                except:
                    pass # Skip if Streamlit blocks it
        return True
    return False
def save_client_data(client_name):
    conn = sqlite3.connect('clients_kyc.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kyc_records 
                 (client_name TEXT PRIMARY KEY, data_json TEXT)''')
    
    # Define a list of substrings that identify "UI" elements we don't want to save
    ui_elements = ('btn', 'next', 'back', 'submit', 'gen_')
    
    save_data = {}
    for k, v in st.session_state.items():
        # Only save if it's NOT a UI element AND not a internal/view key
        if not any(word in k.lower() for word in ui_elements) and \
           not k.startswith('__') and k != "view":
            save_data[k] = v
            
    json_data = json.dumps(save_data, default=str)
    
    c.execute("INSERT OR REPLACE INTO kyc_records VALUES (?, ?)", (client_name, json_data))
    conn.commit()
    conn.close()
    st.success(f"Successfully saved {client_name}")
MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# Universal date limits
MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)

# --- 2. PDF GENERATOR ENGINE ---
class KYC_PDF(FPDF):
    def draw_rect_row(pdf, label, value, label_w=65, value_w=125, h=10):
      curr_x = pdf.get_x()
      curr_y = pdf.get_y()
    
    # Draw Left Label (Bold)
      pdf.set_font("Arial", 'B', 9)
      pdf.multi_cell(label_w, h, f" {label}", border=1)
    
    # Calculate how tall the left box became
      end_y_label = pdf.get_y()
    
    # Reset to draw Right Value
      pdf.set_xy(curr_x + label_w, curr_y)
      pdf.set_font("Arial", '', 9)
      pdf.multi_cell(value_w, h, f" {value}", border=1)
     
    # Calculate how tall the right box became
      end_y_value = pdf.get_y()
     
    # Set Y to the bottom of the tallest box to prevent overlapping the next row
      final_y = max(end_y_label, end_y_value)
      pdf.set_xy(curr_x, final_y)
    def header(self):
        if self.page_no() == 1:
            self.set_font("Arial", 'B', 10)
            self.cell(0, 5, "BG CONSULTANCY PTE. LTD.", ln=True)
            self.set_font("Arial", '', 8)
            self.cell(0, 5, "10 Jalan Besar, #09-03 Sim Lim Tower, Singapore 208787", ln=True)
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
def create_pdf_report(client_name):
    pdf = KYC_PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- 1. COMPANY DETAILS ---
    pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " Company Details", ln=True, fill=True, border=1)
    
    # Row: Company Name
    draw_rect_row(pdf, "Company Name", str(st.session_state.get('kyc_co_name', client_name)))
    
    # Row: Date of Incorporation (SEPARATE)
    inc_date = st.session_state.get('kyc_inc_date')
    fmt_date = inc_date.strftime('%d/%m/%Y') if inc_date else ""
    draw_rect_row(pdf, "Date of Incorporation", fmt_date)
    
    # Row: Company Number (UEN) (SEPARATE)
    uen = st.session_state.get('kyc_co_no', '')
    draw_rect_row(pdf, "Company Number (UEN)", uen)
    
    # Row: Year End Date
    draw_rect_row(pdf, "Year End Date", str(st.session_state.get('kyc_year_end', '')))
    
    # Row: Proposed Company Activity
    act_full = f"{st.session_state.get('kyc_act_main', '')}\n{st.session_state.get('kyc_act_sec', '')}"
    draw_rect_row(pdf, "Proposed Company Activity", act_full)
    
    pdf.ln(5)
   

    # --- 2. DIRECTORS DETAILS ---
    # --- 2. DIRECTORS DETAILS (Fixed Table) ---
    num_dirs = st.session_state.get("num_directors", 1)
    for i in range(num_dirs):
        # Header check for page break
        if pdf.get_y() > 200: pdf.add_page()
        
        pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, " Director Details", ln=True, fill=True, border=1)
        
        # Using the helper to ensure perfect rectangles
        draw_rect_row(pdf, "Name as per Passport / NRIC", str(st.session_state.get(f"d_name_{i}", "")))
        draw_rect_row(pdf, "NRIC / Passport No.", str(st.session_state.get(f"d_id_{i}", "")))
        
        d_dob = st.session_state.get(f"d_dob_{i}")
        fmt_dob = d_dob.strftime('%d/%m/%Y') if d_dob else ""
        draw_rect_row(pdf, "Date of Birth", fmt_dob)
        
        draw_rect_row(pdf, "Email address", str(st.session_state.get(f"d_email_{i}", "")))
        draw_rect_row(pdf, "Mobile Number", str(st.session_state.get(f"d_mobile_{i}", "")))
        draw_rect_row(pdf, "Nationality", str(st.session_state.get(f"d_nat_{i}", "")))
        
        # Address (Helper handles long addresses without breaking the rectangle)
        draw_rect_row(pdf, "Address", str(st.session_state.get(f"d_address_{i}", "")))
        
        pdf.ln(8)
    # --- 3. SHAREHOLDER AND BENEFICIAL OWNERSHIP ---
    # --- 3. SHAREHOLDER AND BENEFICIAL OWNERSHIP (Fixed Table) ---
    num_sh = st.session_state.get("num_shareholders", 1)
    for j in range(num_sh):
        # Header check for page break
        if pdf.get_y() > 200: pdf.add_page()
        
        # Using the blue-ish fill color you specified (220, 235, 252)
        pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(220, 235, 252)
        pdf.cell(0, 10, " Shareholder and Beneficial Ownership", ln=True, fill=True, border=1)
        
        # Perfect rectangle rows using the helper
        draw_rect_row(pdf, "Name as per Passport / NRIC", str(st.session_state.get(f"s_name_{j}", "")))
        draw_rect_row(pdf, "NRIC / Passport No.", str(st.session_state.get(f"s_id_{j}", "")))
        
        s_dob = st.session_state.get(f"s_dob_{j}")
        fmt_s_dob = s_dob.strftime('%d/%m/%Y') if s_dob else ""
        draw_rect_row(pdf, "Date of Birth", fmt_s_dob)
        
        draw_rect_row(pdf, "Email address", str(st.session_state.get(f"s_email_{j}", "")))
        draw_rect_row(pdf, "Nationality", str(st.session_state.get(f"s_nat_{j}", "")))
        
        # Address (Handles multi-line wrapping without breaking the rectangle)
        draw_rect_row(pdf, "Residential Address", str(st.session_state.get(f"s_address_{j}", "")))
        
        pdf.ln(8)

    # --- 4. PERCENTAGE OF SHAREHOLDING ---
    if pdf.get_y() > 180: pdf.add_page()
    pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " Percentage of shareholding Details", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(12, 10, " S.NO.", border=1, align='C'); pdf.cell(50, 10, " Shareholder Name", border=1, align='C')
    pdf.cell(30, 10, " Share of %", border=1, align='C'); pdf.cell(32, 10, " No. applied", border=1, align='C')
    pdf.cell(32, 10, " No. issued", border=1, align='C'); pdf.cell(34, 10, " Paid Up Amount", border=1, align='C', ln=True)
    pdf.set_font("Arial", '', 8)
    for k in range(num_sh):
        pdf.cell(12, 10, str(k+1), border=1, align='C')
        pdf.cell(50, 10, str(st.session_state.get(f"s_name_{k}", "")), border=1)
        pdf.cell(30, 10, str(st.session_state.get(f"p_perc_{k}", "")), border=1, align='C')
        pdf.cell(32, 10, str(st.session_state.get(f"p_applied_{k}", "")), border=1, align='C')
        pdf.cell(32, 10, str(st.session_state.get(f"p_issued_{k}", "")), border=1, align='C')
        pdf.cell(34, 10, str(st.session_state.get(f"p_paid_{k}", "")), border=1, align='C', ln=True)
# --- 5. CONTACTS & CAP (Secretary, CEO, Auth, Capital) ---
    if pdf.get_y() > 180: pdf.add_page()
    
    # 5a. Share Capital (2-column layout)
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " Share Capital", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(95, 8, " Currency", border=1, align='C')
    pdf.cell(95, 8, " Amount", border=1, align='C', ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 10, f" {st.session_state.get('cap_currency', 'SGD')}", border=1, align='C')
    pdf.cell(95, 10, f" {st.session_state.get('cap_amount', '')}", border=1, align='C', ln=True)

    # 5b. CEO Details (Multi-column with Address wrapping)
    pdf.ln(5); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " CEO Details", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'B', 8)
    h_head = 8
    pdf.cell(35, h_head, " Name", border=1); pdf.cell(30, h_head, " ID", border=1)
    pdf.cell(30, h_head, " Mobile", border=1); pdf.cell(40, h_head, " Email", border=1)
    pdf.cell(55, h_head, " Address", border=1, ln=True)

    # Calculate Height for CEO Row
    pdf.set_font("Arial", '', 8)
    c_addr = str(st.session_state.get('ceo_address', ''))
    # Calculate how many lines the address takes
    c_lines = pdf.multi_cell(55, 5, c_addr, split_only=True)
    c_row_h = max(10, len(c_lines) * 5)
    c_y = pdf.get_y()

    pdf.cell(35, c_row_h, str(st.session_state.get('ceo_name', '')), border=1)
    pdf.cell(30, c_row_h, str(st.session_state.get('ceo_id', '')), border=1)
    pdf.cell(30, c_row_h, str(st.session_state.get('ceo_mobile', '')), border=1)
    pdf.cell(40, c_row_h, str(st.session_state.get('ceo_email', '')), border=1)
    # The address cell
    pdf.multi_cell(55, 5 if len(c_lines) > 1 else c_row_h, c_addr, border=1)
    pdf.set_y(c_y + c_row_h)

    # 5c. Authorised Person
    pdf.ln(5); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " Authorised person to contact", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(65, 8, " Name", border=1); pdf.cell(60, 8, " Mobile", border=1); pdf.cell(65, 8, " Email", border=1, ln=True)
    pdf.set_font("Arial", '', 8)
    pdf.cell(65, 10, str(st.session_state.get('auth_name', '')), border=1)
    pdf.cell(60, 10, str(st.session_state.get('auth_mobile', '')), border=1)
    pdf.cell(65, 10, str(st.session_state.get('auth_email', '')), border=1, ln=True)

    # 5d. Company Secretary (Multi-column with Address wrapping)
    pdf.ln(5); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " Company Secretary", ln=True, fill=True, border=1)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(40, 8, " Name", border=1); pdf.cell(30, 8, " ID No.", border=1)
    pdf.cell(85, 8, " Address", border=1); pdf.cell(35, 8, " Nationality", border=1, ln=True)

    # Calculate Height for Secretary Row
    pdf.set_font("Arial", '', 8)
    s_addr = str(st.session_state.get('sec_address', ''))
    s_lines = pdf.multi_cell(85, 5, s_addr, split_only=True)
    s_row_h = max(10, len(s_lines) * 5)
    s_y = pdf.get_y()

    pdf.cell(40, s_row_h, str(st.session_state.get('sec_name', '')), border=1)
    pdf.cell(30, s_row_h, str(st.session_state.get('sec_id', '')), border=1)
    # The multi-line address cell
    pdf.set_xy(80, s_y) # Move to start of address column
    pdf.multi_cell(85, 5 if len(s_lines) > 1 else s_row_h, s_addr, border=1)
    # Nationality
    pdf.set_xy(165, s_y)
    pdf.cell(35, s_row_h, str(st.session_state.get('sec_nat', '')), border=1, ln=True)

    # --- 6. OFFICE & BANK ---
    if pdf.get_y() > 200: pdf.add_page()
    # Registered Office
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, " Registered Office", ln=True, fill=True, border=1); pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 8, str(st.session_state.get('reg_office_address', '')), border=1)
    # Secretarial Records
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, " Secretarial Records", ln=True, fill=True, border=1); pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 8, str(st.session_state.get('sec_records_address', '')), border=1)
    # Bank
    if pdf.get_y() > 220: pdf.add_page()
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " Bank Account", ln=True, fill=True, border=1)
    
    pdf.set_font("Arial", '', 9)
    
    # Row 1: Preferred Bank Name
    # Matches your key: "bank_name"
    pdf.cell(65, 10, " Preferred bank account name", border=1)
    pdf.cell(125, 10, str(st.session_state.get('bank_name', '')), border=1, ln=True)
    
    # Row 2: Currency of Account
    # Matches your key: "bank_account_currency"
    pdf.cell(65, 10, " Currency of account", border=1)
    
    # We fetch specifically from 'bank_account_currency'
    bank_curr = st.session_state.get('bank_account_currency', '')
    pdf.cell(125, 10, str(bank_curr), border=1, ln=True)
    pdf.ln(8)
    num_sh = st.session_state.get("num_shareholders", 1)
    for j in range(num_sh):
        if pdf.get_y() > 200: pdf.add_page()
        
        pdf.set_font("Arial", 'B', 11); pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, " Current Employment/Business particulars", ln=True, fill=True, border=1)
        
        # Table Header
        pdf.set_font("Arial", 'B', 7)
        h_head = 10
        widths = [35, 45, 45, 32, 33] 
        pdf.cell(widths[0], h_head, " BO'S Name", border=1, align='C')
        pdf.cell(widths[1], h_head, " Company Name", border=1, align='C')
        pdf.cell(widths[2], h_head, " Business Nature", border=1, align='C')
        pdf.cell(widths[3], h_head, " Years in emp.", border=1, align='C')
        pdf.cell(widths[4], h_head, " Years of exp.", border=1, align='C', ln=True)
        
        # 1. Prepare Data & Calculate Dynamic Row Height
        pdf.set_font("Arial", '', 8)
        sh_name = str(st.session_state.get(f"s_name_{j}", "")).upper()
        co_name = str(st.session_state.get(f"emp_co_{j}", ""))
        nature = str(st.session_state.get(f"emp_ind_{j}", ""))
        
        # Ghost render to find tallest cell
        lines_name = len(pdf.multi_cell(widths[0], 5, sh_name, split_only=True))
        lines_co = len(pdf.multi_cell(widths[1], 5, co_name, split_only=True))
        lines_nat = len(pdf.multi_cell(widths[2], 5, nature, split_only=True))
        
        # Set unified height (ensures all boxes match the longest text)
        row_h = max(12, lines_name * 5, lines_co * 5, lines_nat * 5)
        start_y = pdf.get_y()
        start_x = 10 

        # 2. DRAW ALL BORDERS FIRST (This locks the rectangle)
        pdf.cell(widths[0], row_h, "", border=1)
        pdf.cell(widths[1], row_h, "", border=1)
        pdf.cell(widths[2], row_h, "", border=1)
        pdf.cell(widths[3], row_h, "", border=1)
        pdf.cell(widths[4], row_h, "", border=1)

        # 3. OVERLAY TEXT (Using set_xy to put text inside the locked boxes)
        # BO Name
        pdf.set_xy(start_x, start_y)
        pdf.multi_cell(widths[0], 5 if lines_name > 1 else row_h, sh_name, align='C')
        
        # Company Name
        pdf.set_xy(start_x + widths[0], start_y)
        pdf.multi_cell(widths[1], 5 if lines_co > 1 else row_h, co_name, align='C')
        
        # Business Nature
        pdf.set_xy(start_x + widths[0] + widths[1], start_y)
        pdf.multi_cell(widths[2], 5 if lines_nat > 1 else row_h, nature, align='C')
        
        # Years Emp & Exp (Simple text)
        pdf.set_xy(start_x + widths[0] + widths[1] + widths[2], start_y)
        pdf.cell(widths[3], row_h, str(st.session_state.get(f"emp_yrs_{j}", "")), align='C')
        
        pdf.set_xy(start_x + sum(widths[:4]), start_y)
        pdf.cell(widths[4], row_h, str(st.session_state.get(f"emp_exp_{j}", "")), align='C')
        
        # 4. Reset cursor to next section
        pdf.set_y(start_y + row_h)
        pdf.ln(5)
    # --- 14. BO'S SOURCE OF WEALTH (EXACT PHOTO MATCH) ---
    num_sh = st.session_state.get("num_shareholders", 1)
    for j in range(num_sh):
        if pdf.get_y() > 200: pdf.add_page()
        
        # Header: BO'S SOURCE OF WEALTH (NAME)
        sh_name = str(st.session_state.get(f"s_name_{j}", "")).upper()
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, f"BO'S SOURCE OF WEALTH ({sh_name})", ln=True)
        pdf.ln(2)

        # Exact labels and descriptions from the photo
        sow_items = [
            ("salary", "Salary/Bonus Income (Annual) Name of the employer, position and annual salary"),
            ("shares", "Owner of Shares in Business Name of the company, website, annual salary"),
            ("inheritance", "Inheritance or Gift Name of the deceased/donor, type of business/investment,\nrelationship, amount received"),
            ("investment", "Investment Name of the investment manager, value of portfolio, origin of investment\nfunds"),
            ("sale", "Sale of Assets/Shares Type of assets/shares, date of sale, value of sale"),
            ("others", "Others (Please provide details )")
        ]

        for sow_key, full_label in sow_items:
            # Check if this item was selected in your Streamlit app
            is_checked = st.session_state.get(f"sow_chk_{j}_{sow_key}", False)
            detail_text = st.session_state.get(f"sow_txt_{j}_{sow_key}", "")

            curr_y = pdf.get_y()
            
            # Draw Checkbox Square
            pdf.set_line_width(0.3)
            if is_checked:
                # Teal background for checked boxes as seen in photo
                pdf.set_fill_color(70, 160, 150) 
                pdf.rect(12, curr_y + 1, 5, 5, 'DF')
                # White Checkmark (simple 'v')
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 8)
                pdf.text(13, curr_y + 4.5, "v")
                pdf.set_text_color(0, 0, 0) # Reset
            else:
                # Empty box
                pdf.set_fill_color(255, 255, 255)
                pdf.rect(12, curr_y + 1, 5, 5, 'D')

            # Render the Label and the Details
            pdf.set_font("Arial", '', 9)
            pdf.set_xy(22, curr_y)
            
            # Combine label and detail if box is checked
            display_text = full_label
            if is_checked and detail_text:
                display_text += f"\nDetails: {detail_text}"
            
            # Use multi_cell to handle the long descriptive text
            pdf.multi_cell(0, 6, display_text)
            
            # Draw a light underline divider as seen in photo
            pdf.set_draw_color(220, 220, 220)
            pdf.line(22, pdf.get_y() + 1, 200, pdf.get_y() + 1)
            pdf.set_draw_color(0, 0, 0) # Reset draw color
            pdf.ln(4)
    # --- 15. DECLARATION/UNDERTAKING (EXACT PHOTO MATCH) ---
    if pdf.get_y() > 180: pdf.add_page()
    pdf.ln(10)
    
    # Section Header
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "Declaration/Undertaking", ln=True)
    pdf.ln(2)
    
    # The 5 specific legal clauses from the photo
    declarations = [
        "1. I/We confirm that the above information is true and accurate, and hereby authorise to supply any or all of such information for due diligence purpose to the Regulators if so requested by them without notification to you.",
        "2. I/We understand the legal and tax reporting requirements and other responsibilities in my/our country of residence and/or other applicable jurisdictions and will company with all the elevant reporting requirements of my /our own. We strongly suggest to seek independent tax advice from a third party tax professional not associated with our company with respect the incorporation or investments.",
        "3. I/we understand and agree that all documents supplied including this form will not be returned to me/us.",
        "4. I/we also undertake to notify us of any future changes to the above information.",
        "5. I/we understand and that we reserves the right to request for additional documentation/information."
    ]
    
    pdf.set_font("Arial", '', 9)
    for dec in declarations:
        # Multi_cell handles the wrapping perfectly for long legal text
        pdf.multi_cell(0, 6, dec)
        # Light grey divider line between points
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(6)
    
    # --- Name of Beneficial Owners Section ---
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "Name of the Beneficial Owner", ln=True)
    pdf.set_font("Arial", '', 10)
    
    num_sh = st.session_state.get("num_shareholders", 1)
    for n in range(num_sh):
        # Fetch name and convert to uppercase to match photo
        bo_name = str(st.session_state.get(f"s_name_{n}", "")).upper()
        if bo_name:
            pdf.ln(2)
            pdf.cell(0, 10, bo_name, ln=True)
            # Underline for each name
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)

    # Final logic to close out the PDF
    # --- 16. SIGNATURE SECTION (EXACT PHOTO MATCH) ---
    # --- 16. UPDATED SIGNATURE SECTION ---
    if pdf.get_y() > 230: pdf.add_page()
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "Signature of Directors / Beneficial Owners", ln=True)
    pdf.ln(5)

    # Collect all unique names from both lists
    all_signatories = []
    
    # Get Directors
    for i in range(st.session_state.get("num_directors", 1)):
        name = st.session_state.get(f"d_name_{i}", "").strip().upper()
        if name and name not in all_signatories:
            all_signatories.append(name)
            
    # Get Shareholders (only add if not already in the list)
    for j in range(st.session_state.get("num_shareholders", 1)):
        name = st.session_state.get(f"s_name_{j}", "").strip().upper()
        if name and name not in all_signatories:
            all_signatories.append(name)

    # Draw signatures 2-across
    for i in range(0, len(all_signatories), 2):
        curr_y = pdf.get_y()
        
        # Left Signature Block
        pdf.set_xy(10, curr_y)
        pdf.line(10, curr_y + 10, 95, curr_y + 10)
        pdf.set_xy(10, curr_y + 12)
        pdf.cell(85, 10, all_signatories[i])
        
        # Right Signature Block
        if i + 1 < len(all_signatories):
            pdf.set_xy(105, curr_y)
            pdf.line(105, curr_y + 10, 190, curr_y + 10)
            pdf.set_xy(105, curr_y + 12)
            pdf.cell(85, 10, all_signatories[i+1])
        
        pdf.ln(25)
    # --- FINAL PDF OUTPUT ---
    return pdf.output(dest='S').encode('latin-1')
def create_minutes_pdf(client_name):
    from fpdf import FPDF
    from datetime import date, datetime
    
    pdf = FPDF()
    # Enable automatic page breaking with a standard margin to prevent spill overflows
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # =========================================================================
    # CRITICAL FIX: Extract session state variables upfront to prevent NameError
    # =========================================================================
    sign_chair = st.session_state.get("res_chairman_sign", "")
    sign_dir = st.session_state.get("res_director_sign", "")
    res_date = st.session_state.get("res_dated_day", date.today())
    
    num_dirs = st.session_state.get("num_directors", 1)
    num_sh = st.session_state.get("num_shareholders", 1)
    inc_date_pdf = st.session_state.get('sec_inc_date_display')
    
    # --- FIXED CONSECUTIVE GRID ROW GENERATOR ---
    def draw_pdf_row(label, value):
        val_str = str(value) if value is not None else ""
        pdf.set_font("Arial", '', 10)
        
        # Calculate exactly how many page rows this string text requires
        lines = pdf.multi_cell(130, 7, f" {val_str}", split_only=True)
        h = max(7, len(lines) * 7)
        
        # Page budget check before rendering borders
        if pdf.get_y() + h > 275:
            pdf.add_page()
            
        y_start = pdf.get_y()
        
        # Left Title Box
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(60, h, f" {label}", border=1)
        
        # Right Value Box placed accurately adjacent to avoid alignment overlapping
        pdf.set_xy(70, y_start) 
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(130, 7, f" {val_str}", border=1)
        pdf.set_y(y_start + h)

    def fmt_date(d_obj):
        if not d_obj: return ""
        if isinstance(d_obj, (date, datetime)): 
            return d_obj.strftime("%d/%m/%Y")
        return str(d_obj)

    # Initialize Document Flow
    pdf.add_page()

    # =========================================================================
    # PART 1: FIRST DIRECTORS' MINUTES
    # =========================================================================
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 6, "FIRST DIRECTORS' MINUTES", ln=True, align='C')
    pdf.cell(0, 6, client_name.upper(), ln=True, align='C')
    pdf.ln(4)

    # 1. METADATA BLOCK GRID
    draw_pdf_row("Name of Company", client_name.upper())
    draw_pdf_row("Place of Meeting", st.session_state.get('sec_meeting_place', ''))
    
    meet_date_raw = st.session_state.get('sec_meet_date')
    meet_time = str(st.session_state.get('sec_meet_time', ''))
    draw_pdf_row("Date and Time of Meeting", f"{fmt_date(meet_date_raw)} {meet_time}")
    draw_pdf_row("Directors Present", st.session_state.get('sec_dirs_present', ''))
    pdf.ln(4)

    # 1. CHAIRMAN
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "1. CHAIRMAN", ln=True)
    pdf.set_font("Arial", '', 10)
    chairman_name = st.session_state.get('sec_chairman_name', '')
    pdf.multi_cell(0, 5, f"The Chair was taken by {chairman_name}")
    pdf.ln(4)

    # 2. INCORPORATION
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "2. INCORPORATION", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "It was noted that the Company was incorporated under the COMPANIES ACT. (CAP.50).")
    pdf.ln(2)
    
    uen_pdf = st.session_state.get('sec_inc_no', '')
    draw_pdf_row("The Certificate of Incorporation number was:", uen_pdf)
    draw_pdf_row("The Date of Incorporation was:", fmt_date(inc_date_pdf))
    
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "A Copy of Constitution was also presented to the meeting.")
    pdf.ln(4)

    # 3. DIRECTORS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "3. DIRECTORS", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "It was resolved that the following be appointed as the first director(s) of the Company:")
    pdf.ln(2)
    
    for i in range(num_dirs):
        d_name = st.session_state.get(f"sec_dir_name_{i}", "")
        if d_name:
            pdf.cell(10, 5, "-", align='C')
            pdf.cell(0, 5, d_name.upper(), ln=True)
    pdf.ln(4)

    # 4. SHARE CAPITAL
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "4. SHARE CAPITAL", ln=True)
    pdf.set_font("Arial", '', 10)
    cap_amt_val = st.session_state.get("sec_cap_amt", "")
    pdf.multi_cell(0, 5, f"It was noted that the share capital of the Company was {cap_amt_val} divided into {cap_amt_val} shares of $1 each.")
    pdf.ln(4)

    # 5. APPLICATION FOR ALLOTMENT OF SHARES
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, f"5. Application for allotment of {client_name.upper()}", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "The application(s) for shares in the Company were submitted as per A attached. It was resolved that the application(s) be approved and that the share(s) be issued accordingly.")
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "Application for and allotment of shares", ln=True)
    pdf.ln(1)
    
    # Table Headings
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(80, 6, " Name of the Shareholder", border=1)
    pdf.cell(60, 6, " NRIC/Passport No", border=1)
    pdf.cell(50, 6, " No. of shares Issued", border=1, ln=True)
    
    pdf.set_font("Arial", '', 9)
    for j in range(num_sh):
        name = st.session_state.get(f"sec_sh_name_{j}", "")
        nric = st.session_state.get(f"sec_sh_id_{j}", "")
        qty = st.session_state.get(f"sec_sh_qty_{j}", "")
        if name or nric:
            pdf.cell(80, 6, f" {name.upper()}", border=1)
            pdf.cell(60, 6, f" {nric}", border=1)
            pdf.cell(50, 6, f" {qty}", border=1, ln=True)
            
    pdf.ln(2)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "It was further resolved that the common seal of the Company be affixed to the share certificate(s) to be issued and that details be entered in the Register of Members.")
    pdf.ln(4)

    # 6. REGISTERED OFFICE AND CORRESPONDENCE ADDRESS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "6. Registered office and correspondence Address", ln=True)
    pdf.set_font("Arial", '', 10)
    reg_office = st.session_state.get('sec_reg_office', '')
    corr_office = st.session_state.get('sec_corr_office', '')
    pdf.multi_cell(0, 5, f"It was resolved that the registered office of the company be situated at:\n{reg_office}")
    pdf.ln(2)
    pdf.multi_cell(0, 5, f"It was resolved that the address to be used for all correspondence be as follows:\n{corr_office}")
    pdf.ln(4)

    # 7. SECRETARY
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "7. Secretary", ln=True)
    pdf.set_font("Arial", '', 10)
    sec_name = st.session_state.get("sec_secretary_name", "")
    pdf.multi_cell(0, 5, f"It was resolved that {sec_name} be appointed as Secretary")
    pdf.ln(4)

    # 8. LOCATION OF BOOKS AND RECORDS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "8. Location of books and records", ln=True)
    pdf.set_font("Arial", '', 10)
    books_place = st.session_state.get("sec_meeting_place", "")
    pdf.multi_cell(0, 5, f"It was resolved that the books, records and minutes of the Company be kept at the following location, until otherwise determined by the director(s):\n{books_place}")
    pdf.ln(4)

    # 9. TERMINATION (Section 1 Meeting Closure)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "TERMINATION", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, "There being no further business, the meeting was terminated with a vote of thanks to the Chair.")
    pdf.ln(12)

    # First Minutes Signature Block placement
    if pdf.get_y() > 240:
        pdf.add_page()
        
    y_sig_first = pdf.get_y()
    pdf.set_xy(10, y_sig_first)
    pdf.cell(85, 4, "........................................................................", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_x(10)
    pdf.cell(85, 5, f"CHAIRMAN: {sign_chair.upper() if sign_chair else '_______________________'}", ln=True)
    
    pdf.set_xy(110, y_sig_first)
    pdf.cell(85, 4, "........................................................................", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_xy(110, y_sig_first + 4)
    pdf.cell(85, 5, f"DIRECTOR: {sign_dir.upper() if sign_dir else '_______________________'}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Dated This Day Of: {fmt_date(res_date)}", ln=True)

    # =========================================================================
    # PART 2: FORM 45 - CONSENT TO ACT AS DIRECTOR
    # =========================================================================
    for i in range(num_dirs):
        f45_name = st.session_state.get(f"f45_name_{i}", "")
        f45_id = st.session_state.get(f"f45_id_{i}", "")
        f45_uen = st.session_state.get(f"f45_uen_{i}", "")
        f45_addr = st.session_state.get(f"f45_address_{i}", "")
        f45_app_date = st.session_state.get(f"f45_app_date_{i}", date.today())
        f45_witness = st.session_state.get(f"f45_witness_{i}", "")

        pdf.ln(6)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 7, "FORM 45: CONSENT TO ACT AS DIRECTOR", ln=True)
        pdf.ln(2)

        draw_pdf_row("Name of Director", f45_name.upper())
        draw_pdf_row("NRIC / Passport No.", f45_id)
        draw_pdf_row("Company Name", client_name.upper())
        draw_pdf_row("Company No. (UEN)", f45_uen)
        draw_pdf_row("Residential Address", f45_addr)
        draw_pdf_row("Date of Appointment", fmt_date(f45_app_date))
        pdf.ln(3)

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 5, "Statutory Declaration Under Singapore Companies Act:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, 
            "1. I hereby consent to act as director of the above-named company with effect from the incorporation date.\n"
            "2. I declare that I am not disqualified from acting as a director under any relevant legal provisions of the Act."
        )
        pdf.ln(4)
        pdf.cell(0, 5, "Signature: .............................................................  Date: ............................", ln=True)

        # Continuation Sheet Wording
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 5, "Form 45 Continuation Sheet I", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5,
            "(8) That the statements made by me in this form are true. I read and understand English. "
            "I confirm that the statements are true, I am also aware that I can be prosecuted in Court if I wilfully give any information on this form which is false."
        )
        pdf.ln(3)
        pdf.cell(0, 5, f"Signature of Director: {f45_name.upper() if f45_name else '_______________________'}", ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", 'I', 9)
        pdf.multi_cell(0, 4.5, f"I certify that the individual named above appeared before me, executed this statement, and verified their identification profile to me.\nCertified By Witness: {f45_witness.upper()}")

    # =========================================================================
    # PART 3: REGISTER OF DIRECTORS
    # =========================================================================
    for i in range(num_dirs):
        f45_name = st.session_state.get(f"f45_name_{i}", "")
        f45_id = st.session_state.get(f"f45_id_{i}", "")
        f45_addr = st.session_state.get(f"f45_address_{i}", "")
        
        pdf.ln(6)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 7, f"REGISTER OF DIRECTORS (Folio No. {i+1})", ln=True)
        pdf.ln(2)

        draw_pdf_row("Full Name Registered", f45_name.upper())
        draw_pdf_row("Identity Number (NRIC / Passport)", f45_id)
        draw_pdf_row("Residential Address", f45_addr)
        draw_pdf_row("Date of Original Appointment", fmt_date(st.session_state.get(f"f45_app_date_{i}", "")))
        draw_pdf_row("Date of Cessation", "ACTIVE / OPEN")

    # =========================================================================
    # PART 4: STATUTORY TRANSACTION RECORD: ALLOTMENT OF SHARES
    # =========================================================================
    for j in range(num_sh):
        sh_name = st.session_state.get(f"sec_sh_name_{j}", "")
        sh_id = st.session_state.get(f"sec_sh_id_{j}", "")
        sh_qty = st.session_state.get(f"sec_sh_qty_{j}", "")
        
        pdf.ln(6)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 7, f"APPLICATION FOR AND ALLOTMENT OF SHARES (Record #{j+1})", ln=True)
        pdf.ln(2)
        
        draw_pdf_row("Name of the Shareholder", sh_name.upper())
        draw_pdf_row("NRIC/Passport No", sh_id)
        draw_pdf_row("No. of Shares Allotted", f"{sh_qty} Shares")
        draw_pdf_row("Class of Shares Issued", "ORDINARY")
        draw_pdf_row("Share Certificate Number", f"Cert No. {j+1}")

    # =========================================================================
    # PART 5: REGISTER OF MEMBERS
    # =========================================================================
    for j in range(num_sh):
        sh_name = st.session_state.get(f"sec_sh_name_{j}", "")
        sh_id = st.session_state.get(f"sec_sh_id_{j}", "")
        sh_qty = st.session_state.get(f"sec_sh_qty_{j}", "")
        
        pdf.ln(6)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 7, f"REGISTER OF MEMBERS (Folio Reference #{j+1})", ln=True)
        pdf.ln(2)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(30, 5, "Member Name:", border=0)
        pdf.set_font("Arial", '', 9)
        pdf.cell(70, 5, sh_name.upper(), border=0)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(35, 5, "NRIC/Passport No:", border=0)
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, sh_id, border=0, ln=True)
        pdf.ln(2)
        
        # Log Table 1
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 5, "1. Shares Allotted / Acquired Log", ln=True)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(24, 5, "Date Entry", border=1, align='C')
        pdf.cell(24, 5, "Allotment No", border=1, align='C')
        pdf.cell(24, 5, "Qty Issued", border=1, align='C')
        pdf.cell(24, 5, "Dist. From", border=1, align='C')
        pdf.cell(24, 5, "Dist. To", border=1, align='C')
        pdf.cell(24, 5, "Cert No", border=1, align='C')
        pdf.cell(24, 5, "Paid/Share", border=1, align='C')
        pdf.cell(24, 5, "Total Paid", border=1, align='C', ln=True)
        
        pdf.set_font("Arial", '', 8)
        pdf.cell(24, 5, fmt_date(inc_date_pdf), border=1, align='C')
        pdf.cell(24, 5, f"#{j+1}", border=1, align='C')
        pdf.cell(24, 5, str(sh_qty), border=1, align='C')
        pdf.cell(24, 5, "-", border=1, align='C')
        pdf.cell(24, 5, "-", border=1, align='C')
        pdf.cell(24, 5, f"Cert-{j+1}", border=1, align='C')
        pdf.cell(24, 5, "$1.00", border=1, align='C')
        pdf.cell(24, 5, f"${sh_qty}.00", border=1, align='C', ln=True)

    # =========================================================================
    # PART 6: REGISTER OF TRANSFERS
    # =========================================================================
    for j in range(num_sh):
        pdf.ln(6)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 7, f"REGISTER OF TRANSFERS (Deed #{j+1})", ln=True)
        pdf.ln(2)
        
        draw_pdf_row("Date of Transfer Lodgement", "-")
        draw_pdf_row("No. of Transfer Deed", "-")
        draw_pdf_row("Transferor Name (From)", "-")
        draw_pdf_row("Transferee Name (To)", "-")
        draw_pdf_row("Number of Shares Transferred", "-")

    # =========================================================================
    # PART 7: FORM 45A - CONSENT TO ACT AS SECRETARY
    # =========================================================================
    f45a_name = st.session_state.get("f45a_ui_name", "")
    f45a_id = st.session_state.get("f45a_ui_id", "")
    f45a_addr = st.session_state.get("f45a_ui_address", "")
    f45a_nat = st.session_state.get("f45a_ui_nationality", "")
    f45a_uen = st.session_state.get("f45a_ui_uen", "")

    pdf.ln(6)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 7, "FORM 45A: CONSENT TO ACT AS SECRETARY", ln=True)
    pdf.ln(2)

    draw_pdf_row("Name of the Secretary", f45a_name.upper())
    draw_pdf_row("Identity No. (NRIC / Passport)", f45a_id)
    draw_pdf_row("Nationality", f45a_nat.upper())
    draw_pdf_row("Company Name", client_name.upper())
    draw_pdf_row("Company No. (UEN)", f45a_uen)
    draw_pdf_row("Residential Address", f45a_addr)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "Statutory Statement Under the Provisions of the Singapore Companies Act:", ln=True)
    pdf.set_font("Arial", '', 9.5)
    pdf.multi_cell(0, 4.5,
        "1. I hereby consent to act as a secretary of the company with effect from incorporation.\n"
        "2. I am a qualified person under section 171(1AA) of the Companies Act."
    )
    pdf.ln(3)
    pdf.cell(0, 5, "Signature: .............................................................  Date: ............................", ln=True)

    # Form 45A Continuation sheet integration text flow
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 5, "Form 45A Continuation Sheet I", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5,
        "(3) That the statements made by me in this form are true. I read and understand English. "
        "I confirm that the statements are true, I am also aware that I can be prosecuted if I wilfully give false information."
    )
    pdf.ln(3)
    pdf.cell(0, 5, f"Signature of Secretary: {f45a_name.upper() if f45a_name else '_______________________'}", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", 'I', 9)
    pdf.multi_cell(0, 4.5, "WITNESS CERTIFICATION: I certify that the person named above signed this Consent in my presence.\nRegistered Filing Agent / Secretarial Professional")

    # =========================================================================
    # PART 8: REGISTER OF SECRETARIES
    # =========================================================================
    reg_sec_name = st.session_state.get("reg_sec_name", "")
    reg_sec_id = st.session_state.get("reg_sec_id", "")
    reg_sec_nat = st.session_state.get("reg_sec_nationality", "")
    reg_sec_addr = st.session_state.get("reg_sec_address", "")
    reg_sec_app = st.session_state.get("reg_sec_app_date", date.today())
    reg_sec_cess = st.session_state.get("reg_sec_cess_date", "ACTIVE / OPEN")

    pdf.ln(6)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 7, "REGISTER OF SECRETARIES", ln=True)
    pdf.ln(2)

    draw_pdf_row("Full Official Name", reg_sec_name.upper())
    draw_pdf_row("Identity Card / Passport No.", reg_sec_id)
    draw_pdf_row("Registered Nationality", reg_sec_nat.upper())
    draw_pdf_row("Residential Address", reg_sec_addr)
    draw_pdf_row("Date of Appointment", fmt_date(reg_sec_app))
    draw_pdf_row("Date of Cessation", reg_sec_cess)

    # =========================================================================
    # PART 9: FINAL WRAP CLOSURE RESOLUTION
    # =========================================================================
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 7, "MINUTES OF DIRECTORS' MEETING & RESOLUTIONS", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "TERMINATION", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "There being no further business, the meeting was terminated with a vote of thanks to the Chair.")
    pdf.ln(12)

    # Side-by-side signature elements positioning safely without collisions
    if pdf.get_y() > 240:
        pdf.add_page()
        
    y_sig_final = pdf.get_y()
    
    # Left execution block
    pdf.set_xy(10, y_sig_final)
    pdf.cell(85, 4, "........................................................................", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_x(10)
    pdf.cell(85, 5, f"CHAIRMAN: {sign_chair.upper() if sign_chair else '_______________________'}", ln=True)
    
    # Right execution block
    pdf.set_xy(110, y_sig_final)
    pdf.cell(85, 4, "........................................................................", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_xy(110, y_sig_final + 4)
    pdf.cell(85, 5, f"DIRECTOR: {sign_dir.upper() if sign_dir else '_______________________'}", ln=True)
    
    pdf.ln(8)
    pdf.set_font("Arial", '', 10)
    pdf.set_x(10)
    pdf.cell(0, 5, f"Dated This Day Of: {fmt_date(res_date)}", ln=True)

    return pdf.output(dest='S').encode('latin-1')
# --- 3. KYC FORM SECTION ---
def master_kyc_form(client_name):
    if f"loaded_{client_name}" not in st.session_state:
        if load_client_data(client_name):
            st.session_state[f"loaded_{client_name}"] = True
            st.rerun() # Refresh once to populate the inputs
    
    if st.button("← Back to Client Database"):
        # Clear the 'loaded' flag so it can be re-loaded if we switch clients
        if f"loaded_{client_name}" in st.session_state:
            del st.session_state[f"loaded_{client_name}"]
        st.session_state["view"] = "management"
        st.rerun()
   

    st.markdown("""
        <style>
        .progress-container { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 20px 0; position: relative; }
        .progress-line { position: absolute; top: 45px; left: 5%; right: 5%; height: 4px; background-color: #2E7D32; z-index: 1; }
        .step { text-align: center; z-index: 2; flex: 1; }
        .circle { width: 50px; height: 50px; background-color: #2E7D32; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-weight: bold; font-size: 20px; border: 3px solid #2E7D32; }
        .active-circle { background-color: #2E7D32; color: white; }
        .inactive-circle { background-color: white; color: #2E7D32; border: 3px solid #2E7D32; }
        .label { margin-top: 10px; font-weight: bold; font-size: 14px; color: #2E7D32; }
        </style>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step"><div class="circle active-circle">1</div><div class="label">Master KYC Form</div></div>
            <div class="step"><div class="circle inactive-circle">2</div><div class="label">BG Sec File</div></div>
            <div class="step"><div class="circle inactive-circle">3</div><div class="label">Customer Acceptance Form</div></div>
            
        </div>
        """, unsafe_allow_html=True)

    st.title(f"KYC: {client_name}")

    # NO ST.FORM WRAPPER HERE - This fixes data binding issues
    st.write("### BASIC INFORMATION REQUEST FORM AND KYC")
    st.date_input("Date", value=date.today(), format="DD/MM/YYYY", min_value=MIN_DATE, max_value=MAX_DATE)
    
    st.write("### Company Details")
    st.text_input("Company Name", value=client_name, key="kyc_co_name")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1: st.text_input("Company No.", value="", key="kyc_co_no")
    with col2: st.date_input("Date of incorporation", value=date(2005, 1, 1), format="DD/MM/YYYY", key="kyc_inc_date", min_value=MIN_DATE, max_value=MAX_DATE)
    with col3: st.text_input("Year End Date", value="31 Dec", key="kyc_year_end")

    st.write("#### Proposed Company Activity")
    act_col1, act_col2 = st.columns(2)
    with act_col1: st.text_input("Main Activity", value="Accounting, Audits", key="kyc_act_main")
    with act_col2: st.text_input("Secondary Activity", value="Tax", key="kyc_act_sec")

    st.divider()

    d_head_col, d_add_col, d_rem_col = st.columns([4, 1, 1])
    with d_head_col: st.write("### DIRECTORS DETAILS")
    if d_add_col.button("+ Add Director"):
        st.session_state.num_directors += 1
        st.rerun()
    if d_rem_col.button("- Remove Director"):
        if st.session_state.num_directors > 1:
            st.session_state.num_directors -= 1
            st.rerun()

    for i in range(st.session_state.num_directors):
        st.markdown(f"#### Director {i+1} Particulars")
        d_c1, d_c2, d_c3 = st.columns([2, 1, 1])
        with d_c1: st.text_input(f"Name as per Passport/NRIC", key=f"d_name_{i}")
        with d_c2: st.text_input(f"NRIC/Passport no.", key=f"d_id_{i}")
        with d_c3: st.date_input(f"Date of birth", value=date(1990, 1, 1), key=f"d_dob_{i}", format="DD/MM/YYYY", min_value=MIN_DATE, max_value=MAX_DATE)
        d_c4, d_c5, d_c6 = st.columns([2, 1, 1])
        with d_c4: st.text_input(f"Email address", key=f"d_email_{i}")
        with d_c5: st.text_input(f"Mobile number", key=f"d_mobile_{i}")
        with d_c6: st.text_input(f"Nationality", key=f"d_nat_{i}")
        st.text_area(f"Address", key=f"d_address_{i}", height=70)
        st.write("---")

    st.divider()

    s_head_col, s_add_col, s_rem_col = st.columns([4, 1, 1])
    with s_head_col: st.write("### SHAREHOLDER DETAILS & BENEFICIAL OWNERSHIP")
    if s_add_col.button("+ Add Shareholder"):
        st.session_state.num_shareholders += 1
        st.rerun()
    if s_rem_col.button("- Remove Shareholder"):
        if st.session_state.num_shareholders > 1:
            st.session_state.num_shareholders -= 1
            st.rerun()

    sh_names = []
    for j in range(st.session_state.num_shareholders):
        st.markdown(f"#### Shareholder {j+1} Particulars")
        s_c1, s_c2, s_c3 = st.columns([2, 1, 1])
        with s_c1: 
            name = st.text_input(f"Name as per Passport/NRIC", key=f"s_name_{j}")
            sh_names.append(name if name else f"Shareholder {j+1}")
        with s_c2: st.text_input(f"NRIC/Passport", key=f"s_id_{j}")
        with s_c3: st.date_input(f"Date of Birth", value=date(1990, 1, 1), key=f"s_dob_{j}", format="DD/MM/YYYY", min_value=MIN_DATE, max_value=MAX_DATE)
        s_c4, s_c5, s_c6 = st.columns([2, 1, 1])
        with s_c4: st.text_input(f"Email address", key=f"s_email_{j}")
        with s_c5: st.text_input(f"Mobile Number", key=f"s_mobile_{j}")
        with s_c6: st.text_input(f"Nationality", key=f"s_nat_{j}")
        st.text_area(f"Address", key=f"s_address_{j}", height=70)

        st.write(f"**CURRENT EMPLOYMENT/BUSINESS - {sh_names[j]}**")
        emp_c1, emp_c2 = st.columns(2)
        with emp_c1:
            st.text_input("Company Name", key=f"emp_co_{j}")
            st.text_input("Business Nature/Industry", key=f"emp_ind_{j}")
        with emp_c2:
            st.text_input("Years in employment", key=f"emp_yrs_{j}")
            st.text_input("Years of experience in industry", key=f"emp_exp_{j}")
            st.file_uploader("Upload CV", type=["pdf"], key=f"emp_cv_{j}")

        st.write(f"**SOURCE OF WEALTH - {sh_names[j]}**")
        sow_list = [("Salary/Bonus", "salary"), ("Business Owner", "shares"), ("Inheritance", "inheritance"), ("Investment", "investment"), ("Asset Sale", "sale"), ("Others", "others")]
        for label, sow_key in sow_list:
            sw_c1, sw_c2 = st.columns([2, 1])
            with sw_c1: st.checkbox(label, key=f"sow_chk_{j}_{sow_key}")
            with sw_c2: st.text_area("Details", key=f"sow_txt_{j}_{sow_key}", height=68, label_visibility="collapsed")

       

    st.divider()

    st.write("### PERCENTAGE OF SHAREHOLDING DETAILS")
    for k in range(st.session_state.num_shareholders):
        st.write(f"#### {sh_names[k]}")
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            st.text_input(f"Share of percentage", key=f"p_perc_{k}")
            st.text_input(f"No. of shares applied", key=f"p_applied_{k}")
        with p_c2:
            st.text_input(f"No. of shares issued", key=f"p_issued_{k}")
            st.text_input(f"Paid up amount", key=f"p_paid_{k}")
        st.write("---")

    st.divider()

    st.write("### COMPANY SECRETARY")
    sec_c1, sec_c2 = st.columns([2, 1])
    with sec_c1:
        st.text_input("Name as per passport/NRIC", key="sec_name")
        st.text_area("Address", key="sec_address", height=70)
    with sec_c2:
        st.text_input("NRIC/Passport no.", key="sec_id")
        st.text_input("Nationality", key="sec_nat")

    st.divider()

    st.write("### CEO DETAILS")
    ceo_c1, ceo_c2 = st.columns([2, 1])
    with ceo_c1: st.text_input("Name as per Passport/NRIC", key="ceo_name")
    with ceo_c2: st.text_input("NRIC/Passport", key="ceo_id")
    ceo_c3, ceo_c4 = st.columns(2)
    with ceo_c3: st.text_input("Mobile Number", key="ceo_mobile")
    with ceo_c4: st.text_input("Email address", key="ceo_email")
    st.text_area("Address", key="ceo_address", height=70)

    st.divider()

    st.write("### AUTHORISED PERSON TO CONTACT")
    auth_c1, auth_c2, auth_c3 = st.columns([2, 1, 1])
    with auth_c1: st.text_input("Name as per passport/NRIC", key="auth_name")
    with auth_c2: st.text_input("Mobile number", key="auth_mobile")
    with auth_c3: st.text_input("Email address", key="auth_email")

    st.write("#### SHARE CAPITAL")
    cap_c1, cap_c2 = st.columns(2)
    with cap_c1: st.text_input("Currency", key="cap_currency", value="SGD")
    with cap_c2: st.text_input("Amount", key="cap_amount")

    st.divider()

    st.write("### REGISTERED OFFICE AND SECRETARIAL RECORDS")
    reg_c1, reg_c2 = st.columns(2)
    with reg_c1:
        st.write("#### Registered Office")
        st.text_area("Registered Office Address", key="reg_office_address", height=100)
    with reg_c2:
        st.write("#### Secretarial Records")
        st.text_area("Secretarial Records Address", key="sec_records_address", height=100)

    st.divider()

    st.write("### BANK ACCOUNT")
    bank_col1, bank_col2 = st.columns(2)
    with bank_col1: st.text_input("Preferred Bank Name", key="bank_name")
    with bank_col2: st.text_input("Currency of Account", key="bank_account_currency")

    st.divider()

    st.write("### CORRESPONDENCE ADDRESS")
    st.text_area("Correspondence Address Details", key="correspondence_address", height=100)

    st.divider()

    st.write("### DECLARATION/UNDERTAKING")
    st.info("""
    1. I/We confirm information is true and accurate.
    2. I/We understand the legal and tax reporting requirements.
    3. I/we understand that all documents supplied will not be returned.
    4. I/we undertake to notify of any future changes.
    """)

    # FORM ACTIONS
    
    st.divider()

    # --- ADD THE SAVE AND PDF BUTTONS HERE ---
    st.subheader("Finalize Application")
    col_save, col_pdf = st.columns(2)

    with col_save:
        # This button triggers the function you added at the top
        if st.button("💾 Save Client Information"):
            current_client = st.session_state.get('kyc_co_name', client_name)
            save_client_data(current_client)

    with col_pdf:
        # Trigger PDF generation and provide download button
        if st.button("📄 Generate PDF Report"):
            try:
                pdf_bytes = create_pdf_report(client_name)
                st.download_button(
                    "📥 CLICK TO DOWNLOAD PDF", 
                    data=pdf_bytes, 
                    file_name=f"KYC_{client_name}.pdf", 
                    mime="application/pdf"
                )
                st.success("PDF Generated Successfully!")
            except Exception as e:
                st.error(f"Error preparing PDF: {e}")
    st.divider()
    
    # Simple navigation to the next section
    col_left, col_right = st.columns([4, 1])
    with col_right:
        if st.button("Next: BG Sec File ➡️", key="next_step_btn"):
            st.session_state["view"] = "bg_sec_file"
            st.rerun()
# --- 4. BG SEC FILE SECTION ---
def bg_sec_file_form(client_name):
    # Progress Bar Component Alignment
    st.markdown("""
        <style>
        .progress-container { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 20px 0; position: relative; }
        .progress-line { position: absolute; top: 45px; left: 5%; right: 5%; height: 4px; background-color: #2E7D32; z-index: 1; }
        .step { text-align: center; z-index: 2; flex: 1; }
        .circle { width: 50px; height: 50px; background-color: #2E7D32; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-weight: bold; font-size: 20px; border: 3px solid #2E7D32; }
        .active-circle { background-color: #2E7D32; color: white; }
        .inactive-circle { background-color: white; color: #2E7D32; border: 3px solid #2E7D32; }
        .label { margin-top: 10px; font-weight: bold; font-size: 14px; color: #2E7D32; }
        </style>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step"><div class="circle inactive-circle">1</div><div class="label">Master KYC Form</div></div>
            <div class="step"><div class="circle active-circle">2</div><div class="label">BG Sec File</div></div>
            <div class="step"><div class="circle inactive-circle">3</div><div class="label">Customer Acceptance Form</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.title(f"BG Sec File: {client_name}")
    
    c_h1, c_h2 = st.columns(2)
    c_h1.write("**FIRST DIRECTORS' MINUTES**")
    c_h2.write("**BG CONSULTANCY PTE LTD**")
    st.markdown("---")

    # Layout row grid input template
    def row_input(label, value, key, disabled=False):
        c1, c2 = st.columns([1, 3])
        with c1: st.markdown(f"**{label}**")
        with c2: return st.text_input(label, value=value, key=key, disabled=disabled, label_visibility="collapsed")

    # 1. METADATA SECTION
    row_input("Name of Company", client_name.upper(), "sec_co_name", disabled=True)
    row_input("Place of Meeting", "NO 10, JALAN BESAR, SIM LIM TOWER #09-03, SINGAPORE 208787", "sec_meeting_place")
    
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1: st.markdown("**Date and Time**")
    with col_d2:
        d_c1, d_c2 = st.columns(2)
        d_c1.date_input("Date", value=date.today(), key="sec_meet_date", format="DD/MM/YYYY", label_visibility="collapsed")
        d_c2.text_input("Time", value="10:00 AM", key="sec_meet_time", label_visibility="collapsed")

    num_dirs = st.session_state.get("num_directors", 1)
    dir_list = [st.session_state.get(f"d_name_{i}", "") for i in range(num_dirs) if st.session_state.get(f"d_name_{i}", "")]
    row_input("Directors Present", ", ".join(dir_list), "sec_dirs_present")

    st.markdown("---")
    
    # 2. SECTIONS 1 - 6 BUSINESS LOGIC
    st.write("#### 1. CHAIRMAN")
    default_chair = dir_list[0] if dir_list else ""
    row_input("The Chair was taken by", default_chair, "sec_chairman_name")

    st.write("#### 2. INCORPORATION")
    uen_number = st.session_state.get("kyc_co_no", "")
    inc_date = st.session_state.get("kyc_inc_date", date.today())
    row_input("The Certificate of Incorporation number was:", uen_number, "sec_inc_no")
    
    ci1, ci2 = st.columns([1, 3])
    with ci1: st.markdown("**The Date of Incorporation was:**")
    with ci2: st.date_input("Inc Date", value=inc_date, key="sec_inc_date_display", disabled=True, format="DD/MM/YYYY", label_visibility="collapsed")

    st.write("#### 3. DIRECTORS")
    for i, d_name in enumerate(dir_list):
        row_input(f"Director {i+1}", d_name, f"sec_dir_name_{i}", disabled=True)

    st.write("#### 4. SHARE CAPITAL")
    cap_amt = st.session_state.get("cap_amount", "100")
    sc1, sc2, sc3, sc4 = st.columns([2, 1, 1, 2])
    with sc1: st.write("Share capital of the Company was")
    with sc2: st.text_input("Cap Amt", value=cap_amt, key="sec_cap_amt", label_visibility="collapsed")
    with sc3: st.write("divided into")
    with sc4: st.write(f"{cap_amt} shares of 1 each.")

    st.write(f"#### 5. APPLICATION FOR ALLOTMENT OF {client_name.upper()}")
    h1, h2, h3 = st.columns([2, 2, 1])
    h1.markdown("**Name of Shareholder**")
    h2.markdown("**NRIC/Passport No**")
    h3.markdown("**No. of shares**")
    num_sh = st.session_state.get("num_shareholders", 1)
    for j in range(num_sh):
        sh_name = st.session_state.get(f"s_name_{j}", "")
        sh_id = st.session_state.get(f"s_id_{j}", "")
        sh_qty = st.session_state.get(f"p_issued_{j}", "")
        r1, r2, r3 = st.columns([2, 2, 1])
        r1.text_input(f"s_name_{j}", value=sh_name, key=f"sec_sh_name_{j}", label_visibility="collapsed")
        r2.text_input(f"s_id_{j}", value=sh_id, key=f"sec_sh_id_{j}", label_visibility="collapsed")
        r3.text_input(f"s_qty_{j}", value=sh_qty, key=f"sec_sh_qty_{j}", label_visibility="collapsed")

    st.write("#### 6. REGISTERED OFFICE AND CORRESPONDENCE ADDRESS")
    reg_addr = st.session_state.get("reg_office_address", "")
    st.markdown("**It was resolved that the registered office of the company be situated at:**")
    st.text_input("Reg Office", value=reg_addr, key="sec_reg_office", label_visibility="collapsed")
    st.markdown("**It was resolved that the address to be used for all correspondence be as follows:**")
    st.text_input("Corr Office", value=reg_addr, key="sec_corr_office", label_visibility="collapsed")

    st.markdown("---")
    
    # SECTIONS 7 - 10 MANAGEMENT SECTIONS
    st.write("#### 7. APPOINTMENT OF SECRETARY")
    row_input("Secretary Name", st.session_state.get("sec_secretary_name", "JANAKIRAMAN AYYAPPAN"), "sec_secretary_name")
    row_input("Secretary NRIC/Passport", st.session_state.get("sec_secretary_id", "S7277791C"), "sec_secretary_id")

    st.write("#### 8. APPOINTMENT OF AUDITORS")
    audit_opt = st.radio("Auditor Status", ["Exempt / No Auditor Appointed", "Appoint Audit Firm"], key="sec_audit_status")
    if audit_opt == "Appoint Audit Firm":
        row_input("Audit Firm Name", "", "sec_auditor_name")
    else:
        st.session_state["sec_auditor_name"] = "EXEMPT"

    st.write("#### 9. BANKING ACCOUNT")
    row_input("Bank Name", "DBS BANK LTD", "sec_bank_name")
    row_input("Authorized Signatories", ", ".join(dir_list), "sec_bank_signatories")

    st.write("#### 10. FINANCIAL YEAR END")
    fye_col1, fye_col2 = st.columns(2)
    fye_col1.selectbox("Day", list(range(1, 32)), index=29, key="sec_fye_day")
    fye_col2.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=8, key="sec_fye_month")

    # =========================================================================
    # --- FORM 45: CONSENT TO ACT AS DIRECTOR & CONTINUATION PACKAGE ---
    # =========================================================================
    st.markdown("---")
    st.write("### FORM 45: CONSENT TO ACT AS DIRECTOR")
    st.write("Statutory Form 45 and matching Continuation Sheet tracking for active directors:")

    for i, d_name in enumerate(dir_list):
        if not d_name:
            continue
            
        with st.expander(f"📄 Form 45 Details & Continuation Sheet I: {d_name.upper()}", expanded=(i == 0)):
            st.markdown(f"#### FORM 45: Particulars for Director {i+1}")
            
            # Fetch variables from state
            d_id = st.session_state.get(f"d_id_{i}", "")
            d_addr = st.session_state.get(f"d_address_{i}", reg_addr)
            
            st.text_input("Name of Director", value=d_name, key=f"f45_name_{i}", disabled=True)
            st.text_input("NRIC / Passport No.", value=d_id, key=f"f45_id_{i}")
            st.text_input("Company Name", value=client_name.upper(), key=f"f45_co_name_{i}", disabled=True)
            st.text_input("Company No. (UEN)", value=uen_number, key=f"f45_uen_{i}", disabled=True)
            st.text_area("Residential Address", value=d_addr, key=f"f45_address_{i}", height=68)
            
            col_f1, col_f2 = st.columns(2)
            col_f1.date_input("Date of Appointment", value=inc_date, key=f"f45_app_date_{i}", format="DD/MM/YYYY")
            col_f2.text_input("Witness / Secretarial Professional Agent", value=st.session_state.get("sec_secretary_name", "JANAKIRAMAN AYYAPPAN"), key=f"f45_witness_{i}")
            
            st.markdown("---")
            st.markdown("**Section B: Under the provisions of the Singapore Companies Act, I state as follows:**")
            
            legal_text = """
            1. That I am not less than 21 years of age and that I am of full capacity.
            2. That I am not an undischarged bankrupt in Singapore or in any other foreign jurisdiction.
            3. Within a period of 5 years preceding the date of this statement I have not had any disqualification order made by the High Court of Singapore against me under section 149 or 154(2) of the Act.
            4. That within a period of 5 years preceding the appointment date, I have not been convicted whether within or without Singapore, of any offence involving the promotion, formation or management of a corporation, fraud or dishonesty punishable with imprisonment for 3 months or more, or under section 157 or section 339 of the Act.
            5. By virtue of the foregoing I am not disqualified from acting as a director of the above named company.
            """
            st.caption(legal_text)
            
            # Form 45 Continuation Sheet I Tabular Structure
            st.markdown("---")
            st.markdown("#### Form 45 Continuation Sheet I")
            st.info("*(8) That the statements made by me in this form are true. I read and understand English. I confirm that the statements are true, I am also aware that I can be prosecuted in Court if I wilfully give any information on this form which is false.*")
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.markdown(f"**Director Signature Execution**")
                st.caption(f"Name: {d_name.upper()}")
                st.caption("Signature: `_______________________`")
            with c_col2:
                st.markdown(f"**Witness / Lodging Agent Certification**")
                st.caption(f"Certified By: {st.session_state.get('sec_secretary_name', '').upper()}")
                st.caption("Signature: `_______________________`")

    # =========================================================================

    st.divider()
    # =========================================================================
    # --- STATUTORY LEDGER: REGISTER OF DIRECTORS ---
    # =========================================================================
    st.markdown("---")
    st.write("### STATUTORY BOOK: REGISTER OF DIRECTORS")
    st.write("Official statutory record blocks managed per executive officer assignment:")

    for i, d_name in enumerate(dir_list):
        if not d_name:
            continue
            
        with st.expander(f"🗃️ Register of Directors Ledger Card: {d_name.upper()}", expanded=False):
            st.markdown(f"**REGISTER OF DIRECTORS — FOLIO REFERENCE REFERENCE NO. {i+1}**")
            
            # Fetch variables verified earlier in state
            d_id = st.session_state.get(f"f45_id_{i}", st.session_state.get(f"d_id_{i}", ""))
            d_addr = st.session_state.get(f"f45_address_{i}", st.session_state.get(f"d_address_{i}", reg_addr))
            app_date_raw = st.session_state.get(f"f45_app_date_{i}", inc_date)
            formatted_date = app_date_raw.strftime("%d/%m/%Y") if isinstance(app_date_raw, date) else str(app_date_raw)
            
            # Display information matching your image template tabular parameters exactly
            director_ledger_entries = {
                "Statutory Parameter Column": [
                    "Full Name Registered", 
                    "Identity Number (NRIC / Passport)", 
                    "Residential Address", 
                    "Nationality", 
                    "Business Occupation", 
                    "Date of Original Appointment", 
                    "Date of Cessation / Resignation"
                ],
                "Current Corporate Records Status": [
                    d_name.upper(),
                    d_id,
                    d_addr,
                    st.session_state.get(f"d_nationality_{i}", "SINGAPORE CITIZEN"),
                    st.session_state.get(f"d_occupation_{i}", "DIRECTOR"),
                    formatted_date,
                    "ACTIVE / OPEN"
                ]
            }
            
            st.table(director_ledger_entries)
    # =========================================================================
    # --- STATUTORY LEDGER: APPLICATION FOR & ALLOTMENT OF SHARES ---
    # =========================================================================
    st.markdown("---")
    st.write("### STATUTORY TRANSACTION RECORD: ALLOTMENT OF SHARES")
    st.write("Tracks the individual board authorization and application details for new share issues:")

    num_sh = st.session_state.get("num_shareholders", 1)
    
    for j in range(num_sh):
        sh_name = st.session_state.get(f"sec_sh_name_{j}", st.session_state.get(f"s_name_{j}", ""))
        if not sh_name:
            continue
            
        with st.expander(f"📋 Share Allotment Allotment Card: {sh_name.upper()}", expanded=False):
            st.markdown(f"**APPLICATION FOR AND ALLOTMENT OF SHARES — RECORD NO. {j+1}**")
            
            sh_id = st.session_state.get(f"sec_sh_id_{j}", st.session_state.get(f"s_id_{j}", ""))
            sh_qty = st.session_state.get(f"sec_sh_qty_{j}", st.session_state.get(f"p_issued_{j}", "100"))
            
            # Displays the individual transactional tracking data box
            allotment_ledger_entries = {
                "Allotment Parameter": [
                    "Name of the Shareholder",
                    "NRIC / Passport No.",
                    "No. of Shares Allotted",
                    "Class of Shares",
                    "Certificate Number Assigned",
                    "Date of Allotment Action"
                ],
                "Transaction Record Value": [
                    sh_name.upper(),
                    sh_id,
                    f"{sh_qty} Shares",
                    "ORDINARY",
                    f"Cert No. {j+1}",
                    inc_date.strftime("%d/%m/%Y") if isinstance(inc_date, date) else str(inc_date)
                ]
            }
            st.table(allotment_ledger_entries)
    # =========================================================================
    # --- STATUTORY LEDGER: REGISTER OF MEMBERS (UPDATED FULL THING) ---
    # =========================================================================
    st.markdown("---")
    st.write("### STATUTORY OWNERSHIP RECORD: REGISTER OF MEMBERS")
    st.write("Definitive historical continuous ledger tracking official corporate membership status:")

    for j in range(num_sh):
        sh_name = st.session_state.get(f"sec_sh_name_{j}", st.session_state.get(f"s_name_{j}", ""))
        if not sh_name:
            continue
            
        with st.expander(f"🗃️ Register of Members Legal Folio: {sh_name.upper()}", expanded=False):
            st.markdown(f"### REGISTER OF MEMBERS")
            st.markdown(f"**FOLIO REFERENCE REFERENCE NO. {j+1}**")
            
            # Master Member Meta-data Row
            sh_id = st.session_state.get(f"sec_sh_id_{j}", st.session_state.get(f"s_id_{j}", ""))
            sh_qty = st.session_state.get(f"sec_sh_qty_{j}", st.session_state.get(f"p_issued_{j}", "100"))
            sh_addr = st.session_state.get(f"s_address_{j}", reg_addr)
            sh_nat = st.session_state.get(f"s_nationality_{j}", "SINGAPORE CITIZEN")
            fmt_inc_date = inc_date.strftime("%d/%m/%Y") if isinstance(inc_date, date) else str(inc_date)

            meta_col1, meta_col2 = st.columns(2)
            with meta_col1:
                st.markdown(f"**Name:** {sh_name.upper()}")
                st.markdown(f"**Address:** {sh_addr}")
            with meta_col2:
                st.markdown(f"**NRIC/Passport No:** {sh_id}")
                st.markdown(f"**Nationality:** {sh_nat}")
            
            st.markdown("#### 1. Shares Allotted / Acquired Log")
            # First Grid Matching IMG_0293.jpg Column Structure
            allotted_log_table = {
                "Date of Entry": [fmt_inc_date],
                "No. of Allotment": [f"Allotment #{j+1}"],
                "No. of Shares Allotted": [sh_qty],
                "Distinctive Nos. From": ["0000001"],
                "Distinctive Nos. To": [str(sh_qty).zfill(7)],
                "Certificate No.": [f"Cert No. {j+1}"],
                "Amount Paid per Share": ["$1.00"],
                "Total Paid Up Capital": [f"${sh_qty}.00"]
            }
            st.table(allotted_log_table)

            st.markdown("#### 2. Shares Transferred / Disposed Log")
            # Second Grid Matching IMG_0294.jpg Column Structure
            transferred_log_table = {
                "Date of Transfer": ["-"],
                "No. of Transfer Deed": ["-"],
                "No. of Shares Transferred": ["-"],
                "Distinctive Nos. From": ["-"],
                "Distinctive Nos. To": ["-"],
                "Transferred To (Folio / Name)": ["-"],
                "Balance Shares Held": [sh_qty],
                "Date Ceased to be Member": ["OPEN / ACTIVE OWNER"]
            }
            st.table(transferred_log_table)
    # =========================================================================
    # --- STATUTORY LEDGER: REGISTER OF TRANSFERS ---
    # =========================================================================
    st.markdown("---")
    st.write("### STATUTORY TRANSACTION RECORD: REGISTER OF TRANSFERS")
    st.write("Official register documenting the formal transfer deeds and structural share changes:")

    num_sh = st.session_state.get("num_shareholders", 1)
    
    for j in range(num_sh):
        sh_name = st.session_state.get(f"sec_sh_name_{j}", st.session_state.get(f"s_name_{j}", ""))
        if not sh_name:
            continue
            
        with st.expander(f"📜 Register of Transfers Entry: {sh_name.upper()}", expanded=False):
            st.markdown(f"**REGISTER OF TRANSFERS — TRANSFER TRANSACTION BOOK ENTRY**")
            
            sh_id = st.session_state.get(f"sec_sh_id_{j}", st.session_state.get(f"s_id_{j}", ""))
            sh_qty = st.session_state.get(f"sec_sh_qty_{j}", st.session_state.get(f"p_issued_{j}", "100"))
            
            # Formatted data entry matrix matching the tabular column headers from IMG_0295.jpg exactly
            transfer_ledger_entries = {
                "Statutory Transfer Parameter": [
                    "Date of Transfer Lodgement",
                    "No. of Transfer Deed",
                    "Transferor Name (From Whom Transferred)",
                    "Transferee Name (To Whom Transferred)",
                    "Number of Shares Transferred",
                    "Distinctive Numbers From",
                    "Distinctive Numbers To",
                    "New Certificate Number Issued"
                ],
                "Current Transaction Status": [
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-"
                ]
            }
            st.table(transfer_ledger_entries)
            st.caption("ℹ️ *Note: At incorporation, all initial share allocations are logged inside the Allotment Ledger. The Register of Transfers remains clear until a secondary sale or assignment takes place.*")
    # NAVIGATION AND DATA EXPORT CONTROL BUTTONS
    # =========================================================================
# =========================================================================
    # --- FORM 45A: CONSENT TO ACT AS SECRETARY & CONTINUATION SHEET ---
    # =========================================================================
    st.markdown("---")
    st.write("### FORM 45A: CONSENT TO ACT AS SECRETARY")
    st.write("Official Form 45A statutory declaration layout with qualification criteria selections:")

    with st.expander("📄 Form 45A Details & Continuation Sheet I: Secretary Setup", expanded=True):
        st.markdown("#### FORM 45A: Particulars of Secretary")
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.text_input("Name of Secretary", value="", key="f45a_ui_name")
            st.text_input("Company Name", value=client_name.upper(), key="f45a_ui_co_name", disabled=True)
            st.text_area("Residential Address", value="", key="f45a_ui_address", height=68)
        with s_col2:
            st.text_input("Identity No. (NRIC / Passport No.)", value="", key="f45a_ui_id")
            st.text_input("Company No. (UEN)", value="", key="f45a_ui_uen")
            st.text_input("Nationality", value="", key="f45a_ui_nationality")

        st.markdown("---")
        st.markdown("**Statutory Declarations (Under the provisions of the Singapore Companies Act):**")
        st.write("*I, the under mentioned person, hereby consent to act as a secretary of the above named company with effect from the date of incorporation.*")
        
        st.markdown("##### I am a qualified person under section 171(1AA) of the Companies Act by virtue of my being (Select applicable):")
        
        # Statutory selections matching standard ACRA Form 45A layout parameters exactly
        st.checkbox("*(i) a secretary of a company for at least 3 of the 5 years immediately preceding the above mentioned date of my appointment as secretary of the above named company*", key="f45a_crit_1")
        st.checkbox("*(ii) a qualified person under the Legal Profession Act (Cap. 161)*", key="f45a_crit_2")
        st.checkbox("*(iii) a public accountant*", key="f45a_crit_3")
        st.checkbox("*(iiia) a member of the Institute of Certified Public Accountants in Singapore*", key="f45a_crit_4")
        st.checkbox("*(iv) a member of the Singapore Association of the Institute of Chartered Secretaries and Administrators*", key="f45a_crit_5")
        st.checkbox("*(v) a member of the Association of International Accountants (Singapore Branch)*", key="f45a_crit_6")
        st.checkbox("*(vi) a member of the Institute of Company Accountants, Singapore*", key="f45a_crit_7")

        # Form 45A Continuation Sheet I Phrasing Layout
        st.markdown("---")
        st.markdown("#### Form 45A Continuation Sheet I")
        st.info("*(3) That the statements made by me in this form are true. I read and understand English. I confirm that the statements are true, I am also aware that I can be prosecuted in Court if I wilfully give any information on this form which is false.*")
        
        sc_col1, sc_col2 = st.columns(2)
        with sc_col1:
            st.markdown(f"**Secretary Signature Block**")
            st.caption("Signature: `_______________________`")
            st.caption("Dated This Day Of: `_______________________`")
        with sc_col2:
            st.markdown(f"**Witness / Lodging Agent Certification**")
            st.caption("Certified By: REGISTERED FILING AGENT")
            st.caption("Signature: `_______________________`")
    # =========================================================================
    # --- STATUTORY LEDGER: REGISTER OF SECRETARIES ---
    # =========================================================================
    st.markdown("---")
    st.write("### STATUTORY BOOK: REGISTER OF SECRETARIES")
    st.write("Official continuous ledger tracking historical and current corporate secretary appointments:")

    with st.expander("🗃️ Register of Secretaries Ledger Card", expanded=True):
        st.markdown("#### REGISTER OF SECRETARIES")
        st.caption("To be completed by secretaries of public companies or by secretaries of private companies appointed under section 171(1AB) of the Act.")
        
        # Capture input parameters as completely empty baseline defaults
        sec_ledger_name = st.text_input("Official Full Name", value="", key="reg_sec_name")
        sec_ledger_id = st.text_input("Identity No. (NRIC / Passport)", value="", key="reg_sec_id")
        sec_ledger_nat = st.text_input("Registered Nationality", value="", key="reg_sec_nationality")
        sec_ledger_addr = st.text_area("Residential Address Record", value="", key="reg_sec_address", height=68)
        
        col_sl1, col_sl2 = st.columns(2)
        with col_sl1:
            sec_ledger_app = col_sl1.date_input("Date of Appointment", value=date.today(), key="reg_sec_app_date", format="DD/MM/YYYY")
        with col_sl2:
            sec_ledger_cess = col_sl2.text_input("Date of Cessation", value="ACTIVE / OPEN", key="reg_sec_cess_date")

        st.markdown("---")
        st.markdown("**Current Ledger Summary Entry View:**")
        
        # Display table representation matching IMG_0298.jpg criteria layout
        sec_ledger_table = {
            "Statutory Book Parameter": [
                "Folio Reference Number",
                "Full Registered Name",
                "Identity Card / Passport Number",
                "Nationality Status",
                "Residential Address Ledger Entry",
                "Official Appointment Date",
                "Official Cessation Date"
            ],
            "Live Database Value": [
                "Folio No. 1",
                sec_ledger_name.upper(),
                sec_ledger_id,
                sec_ledger_nat.upper(),
                sec_ledger_addr,
                sec_ledger_app.strftime("%d/%m/%Y") if isinstance(sec_ledger_app, date) else str(sec_ledger_app),
                sec_ledger_cess
            ]
        }
        st.table(sec_ledger_table)
    st.divider()
    # =========================================================================
    # --- MINUTES OF DIRECTORS' MEETING & RESOLUTION ---
    # =========================================================================
    st.markdown("---")
    st.write("### MINUTES OF DIRECTORS' MEETING & RESOLUTION")

    with st.expander("📝 Minutes Meeting Closure", expanded=True):
        st.markdown("**TERMINATION**")
        st.write("There being no further business, the meeting was terminated with a vote of thanks to the Chair.")
        
        st.markdown("---")
        st.markdown("**SIGNATURE BLOCKS**")
        
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.text_input("Chairman", value="", key="res_chairman_sign")
            st.caption("Signature: `_______________________`")
        with res_col2:
            st.text_input("Director", value="", key="res_director_sign")
            st.caption("Signature: `_______________________`")
            
        st.date_input("Dated This Day Of", value=date.today(), key="res_dated_day", format="DD/MM/YYYY")
    st.markdown("---")
    b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
    
    if b_col1.button("← Back to KYC"):
        st.session_state["view"] = "kyc_form"
        st.rerun()
        
    if b_col2.button("Generate Minutes Package PDF"):
        # Assuming create_minutes_pdf is defined elsewhere in your runtime environment
        pdf_data = create_minutes_pdf(client_name)
        st.download_button("Download Document Package PDF", data=pdf_data, file_name=f"{client_name}_Corporate_Pack.pdf", mime="application/pdf")
        
    if b_col3.button("Next: Customer acceptance form ➡️", key="next_step_btn"):
       st.session_state["view"] = "acceptance_form"
       st.rerun()

def render_customer_acceptance_form(client_name_arg=None):
    import streamlit as st

    # 1. Initialize global company variable safely if not present
    if "selected_client_name" not in st.session_state:
        st.session_state["selected_client_name"] = ""

    # Sync name if it was passed as an argument from the database selection
    if client_name_arg and not st.session_state["selected_client_name"]:
        st.session_state["selected_client_name"] = client_name_arg

    # Initialize counter for Section B dynamic rows
    if "caf_section_b_count" not in st.session_state:
        st.session_state["caf_section_b_count"] = 1

    # 2. Progress Bar Component Custom CSS Injection
    st.markdown("""
        <style>
        .progress-container { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 20px 0; position: relative; }
        .progress-line { position: absolute; top: 45px; left: 10%; right: 10%; height: 4px; background-color: #2E7D32; z-index: 1; }
        .step { text-align: center; z-index: 2; flex: 1; }
        .circle { width: 50px; height: 50px; background-color: #2E7D32; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-weight: bold; font-size: 20px; border: 3px solid #2E7D32; }
        .active-circle { background-color: #2E7D32; color: white; }
        .inactive-circle { background-color: white; color: #2E7D32; border: 3px solid #2E7D32; }
        .label { margin-top: 10px; font-weight: bold; font-size: 14px; color: #2E7D32; }
        </style>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step"><div class="circle inactive-circle">1</div><div class="label">Master KYC Form</div></div>
            <div class="step"><div class="circle inactive-circle">2</div><div class="label">BG Sec File</div></div>
            <div class="step"><div class="circle active-circle">3</div><div class="label">Customer Acceptance Form</div></div>
            <div class="step"><div class="circle inactive-circle">4</div><div class="label">Secretarial Engagement Letter</div></div>
            <div class="step"><div class="circle inactive-circle">5</div><div class="label">Terms and Conditions</div></div>
        </div>
        """, unsafe_allow_html=True)

    # --- TOP CLIENT DETAILS SECTION ---
    st.caption("BGC-CUSTOMER ACCEPTANCE FORM")
    st.subheader("INFORMATION ABOUT CUSTOMERS (BENEFICIAL OWNERS AND POLITICALLY EXPOSED PERSONS)")

    client_status = st.radio(
        "Client Type",
        options=["Existing Client", "New Client"],
        index=1,
        label_visibility="collapsed",
        key="caf_client_status_radio"
    )

    client_name = st.text_input(
        "Name of the Client", 
        value=st.session_state["selected_client_name"],
        key="caf_main_client_name"
    )
    st.session_state["selected_client_name"] = client_name

    # Corporate Pack defaults configurations
    default_uen = "200517609N"
    default_address = "NO 10, JALAN BESAR, SIM LIM TOWER #09-03, SINGAPORE 208787"
    default_inc_date = "01/01/2005"

    if "STAGCO DOUBLEZ" in client_name.upper():
        default_uen = "202546019H"
        default_address = "761 ANG MO KIO AVENUE 2, HORIZON GREEN, SINGAPORE 567792"
        default_inc_date = "15/10/2025"
    elif "DSFGH" in client_name.upper():
        default_uen = ""
        default_address = "NO 10, JALAN BESAR, SIM LIM TOWER #09-03, SINGAPORE 208787"
        default_inc_date = "19/05/2026"

    client_since = st.text_input("Client Since", value="01/01/2005", key="caf_client_since_field")
    referred_by = st.selectbox("Referred by", options=["NA", "Internal Referral", "External Partner"], index=0, key="caf_referred_by_field")
    date_of_inc = st.text_input("Date of Incorporation", value=default_inc_date, key="caf_date_of_inc_field")
    other_info = st.text_input("Other", key="caf_other_info_field")

    st.markdown("---")

    # --- SECTION A (INFORMATION OF CUSTOMER) ---
    st.subheader("SECTION A ( Information of customer )")
    st.markdown("**NEW OR BUSINESS ENTITY'S INFORMATION**")

    entity_name = st.text_input("Name of entity", value=client_name, key="caf_section_a_entity_name")
    inc_reg_num = st.text_input("Incorporation registration number", value=default_uen, key="caf_section_a_inc_reg_num")
    address_office = st.text_area("Address (place of business/registered office)", value=default_address, key="caf_section_a_address_office")
    place_of_reg = st.text_input("Place of registration /incorporation", value="Singapore", key="caf_section_a_place_of_reg")
    date_of_reg = st.text_input("Date of registration /incorporation", value=date_of_inc, key="caf_section_a_date_of_reg")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<font color='red'><b>INTENDED NATURE AND PURPOSE OF BUSINESS RELATIONSHIP REQUIRED</b></font>", unsafe_allow_html=True)
    
    rel_registered_office = st.checkbox("Registered office", value=True, key="caf_rel_reg_office")
    rel_corp_sec = st.checkbox("Acting as corporate Secretary", value=True, key="caf_rel_corp_sec")
    rel_accounting = st.checkbox("Accounting services", value=True, key="caf_rel_accounting")
    rel_taxation = st.checkbox("Taxation services", value=True, key="caf_rel_taxation")
    rel_acra = st.checkbox("ACRA filing services", value=True, key="caf_rel_acra")
    rel_others = st.checkbox("Others", value=False, key="caf_rel_others")

    st.markdown("---")

    # --- SECTION B (DYNAMIC INDIVIDUAL ENTRIES) ---
    st.subheader("SECTION B ( Information on individual Beneficial Owner / Politically Exposed Person )")
    st.caption("Please add individual entries as required:")

    # Loop to generate dynamic user input rows
    for i in range(st.session_state["caf_section_b_count"]):
        st.markdown(f"#### Individual Profile #{i+1}")
        
        b_name = st.text_input(f"Name of individual [{i+1}]", key=f"caf_sec_b_name_{i}")
        b_alias = st.text_input(f"Alias (if any) [{i+1}]", key=f"caf_sec_b_alias_{i}")
        b_id = st.text_input(f"NRIC /Passport number [{i+1}]", key=f"caf_sec_b_id_{i}")
        b_dob = st.text_input(f"Date of birth [{i+1}]", key=f"caf_sec_b_dob_{i}")
        b_nationality = st.text_input(f"Nationality [{i+1}]", key=f"caf_sec_b_nationality_{i}")
        b_address = st.text_area(f"Residential address [{i+1}]", key=f"caf_sec_b_address_{i}", height=68)
        
        st.markdown("<font color='red'><b>Politically Exposed Person (PEP) Status Verified:</b></font>", unsafe_allow_html=True)
        b_pep = st.selectbox(
            f"Is the individual a PEP or an immediate family member/close associate of a PEP? [{i+1}]",
            options=["No", "Yes"],
            index=0,
            key=f"caf_sec_b_pep_{i}"
        )
        st.markdown("<hr style='border-top: 1px dashed #bbb;'>", unsafe_allow_html=True)

    # Dynamic controls row
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 4])
    
    if ctrl_col1.button("➕ Add More"):
        st.session_state["caf_section_b_count"] += 1
        st.rerun()
        
    if ctrl_col2.button("➖ Remove Last") and st.session_state["caf_section_b_count"] > 1:
        st.session_state["caf_section_b_count"] -= 1
        st.rerun()

    # --- BOTTOM FORM EXECUTION ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("SUBMIT NOW", type="primary", use_container_width=True):
        st.success("Customer Acceptance Form & All Individual Section B Profiles Saved Successfully!")
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.title("🔒 Audit Firm Secure Login")
    password = st.text_input("Enter Office Password", type="password")
    if st.button("Login"):
        if password == "Awesome2050@": 
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False

# Initialize Session State
if 'view' not in st.session_state: st.session_state["view"] = "management"
if 'num_directors' not in st.session_state: st.session_state.num_directors = 1
if 'num_shareholders' not in st.session_state: st.session_state.num_shareholders = 1

if check_password():
    
    if st.session_state["view"] == "management":
        st.title("Client Management System")

        df = get_clients()

        if not df.empty:
            df['client_num'] = pd.to_numeric(df['client_num'], errors='coerce')
            df['year_end'] = pd.Categorical(df['year_end'], categories=MONTHS, ordered=True)
            df.columns = [col.replace('_', ' ').upper() for col in df.columns]

            st.subheader("📊 Practice Overview")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Total Clients", len(df))
            m_col2.metric("Active Portfolios", len(df[df['STATUS'] == 'Active']))
            m_col3.metric("Terminated", len(df[df['STATUS'] == 'Terminated']))

            st.divider()

        # --- SIDEBAR (ADD CLIENT) ---
        st.sidebar.header("Add New Client")
        with st.sidebar.form("add_form", clear_on_submit=True):
            new_num = st.number_input("Client Number", min_value=1, step=1)
            new_name = st.text_input("Name of Customer")
            new_uen = st.text_input("UEN Number")
            new_month = st.selectbox("Year End Month", MONTHS)
            new_status = st.selectbox("Status", ["Active", "Terminated"])
            
            if st.form_submit_button("Save New Client"):
                if new_num and new_name:
                    add_client(new_num, new_name, new_uen, new_month, new_status)
                    st.success("Client Added!")
                    st.rerun()
                else:
                    st.error("Fields required.")

        # --- MAIN DISPLAY & SEARCH ---
        if not df.empty:
            st.subheader("📋 Client Database")
            search_query = st.text_input("🔍 Search by Client Name or UEN", "")
            
            filtered_df = df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['NAME'].str.contains(search_query, case=False, na=False) | 
                    filtered_df['UEN'].str.contains(search_query, case=False, na=False)
                ]

            sort_col = st.selectbox("Sort data by:", ["CLIENT NUM", "YEAR END", "NAME"])
            df_sorted = filtered_df.sort_values(by=sort_col)
            
            st.dataframe(df_sorted, use_container_width=True, hide_index=True)
            st.divider()

            # --- EDIT / DELETE SECTION ---
            st.subheader("📝 Edit or Delete Client Details")
            client_options = {f"{row['NAME']} (ID: {row['ID']})": row['ID'] for _, row in filtered_df.iterrows()}
            if client_options:
                selected_option = st.selectbox("Select a client to modify:", list(client_options.keys()))
                selected_id = client_options[selected_option]
                client_info = df[df['ID'] == selected_id].iloc[0]
                
                with st.expander(f"Modify Details for {client_info['NAME']}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_num = st.number_input("Client Number", value=int(client_info['CLIENT NUM']))
                        edit_name = st.text_input("Customer Name", value=str(client_info['NAME']))
                        edit_uen = st.text_input("UEN", value=str(client_info['UEN']))
                    with col2:
                        current_month = str(client_info['YEAR END'])
                        month_idx = MONTHS.index(current_month) if current_month in MONTHS else 0
                        edit_month = st.selectbox("Year End", MONTHS, index=month_idx)
                        
                        status_list = ["Active", "Terminated"]
                        current_status = str(client_info['STATUS'])
                        status_idx = status_list.index(current_status) if current_status in status_list else 0
                        edit_status = st.selectbox("Client Status", status_list, index=status_idx)

                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                    if btn_col1.button("✅ Update Details", type="primary"):
                        update_client(int(client_info['ID']), edit_num, edit_name, edit_uen, edit_month, edit_status)
                        st.success("Updated!")
                        st.rerun()
                        
                    if btn_col2.button("🗑️ Delete Client"):
                        delete_client(int(client_info['ID']))
                        st.warning("Deleted.")
                        st.rerun()

                    if btn_col3.button("📂 Open KYC Form"):
                        st.session_state["selected_client_name"] = client_info['NAME']
                        st.session_state["view"] = "kyc_form"
                        st.rerun()
            else:
                st.info("No clients match your search.")
        else:
            st.info("No clients found.")

    # --- VIEWS FOR KYC FORM FLOW ---
    # --- VIEWS FOR KYC FORM FLOW ---
    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])

    elif st.session_state["view"] == "bg_sec_file":
        bg_sec_file_form(st.session_state["selected_client_name"])

    elif st.session_state["view"] == "acceptance_form":
        render_customer_acceptance_form(st.session_state["selected_client_name"])