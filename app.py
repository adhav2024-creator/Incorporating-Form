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
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "FIRST DIRECTORS' MINUTES", ln=True, align='C')
    pdf.cell(0, 10, client_name.upper(), ln=True, align='C')
    pdf.ln(10)

    def draw_row(label, value):
        pdf.set_font("Arial", 'B', 10)
        # 1. Calculate how many lines the text will take
        pdf.set_font("Arial", '', 10)
        lines = pdf.multi_cell(130, 10, f" {value}", split_only=True)
        # 2. Set row height based on line count
        h = max(10, len(lines) * 10)
        
        y_start = pdf.get_y()
        # 3. Draw Left Box (Label)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(60, h, f" {label}", border=1)
        
        # 4. Draw Right Box (Value)
        pdf.set_xy(70, y_start) # Move to the right of the label
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(130, 10, f" {value}", border=1)
        
        # 5. Reset Y to the bottom of the tallest box
        pdf.set_y(y_start + h)

    # Populate table with session state data
    draw_row("Place of Meeting", st.session_state.get('sec_meeting_place', ''))
    draw_row("Date & Time", f"{st.session_state.get('sec_meeting_date', '')} {st.session_state.get('sec_meeting_time', '')}")
    draw_row("Directors Present", st.session_state.get('sec_dirs_present', ''))
    draw_row("Chairman", st.session_state.get('sec_chairman_name', ''))
    draw_row("Shares Allotted", st.session_state.get('sec_total_shares', ''))

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
    # ... (CSS and Header remain the same) ...
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

    def row_input(label, value, key, disabled=False):
        c1, c2 = st.columns([1, 3])
        with c1: st.markdown(f"**{label}**")
        with c2: st.text_input(label, value=value, key=key, disabled=disabled, label_visibility="collapsed")

    # 1. METADATA
    row_input("Name of Company", client_name.upper(), "sec_co_name", disabled=True)
    row_input("Place of Meeting", "NO 10, JALAN BESAR, SIM LIM TOWER #09-03, SINGAPORE 208787", "sec_meeting_place")
    
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1: st.markdown("**Date and Time**")
    with col_d2:
        d_c1, d_c2 = st.columns(2)
        # DATE FORMAT FIX: Added format="DD/MM/YYYY"
        d_c1.date_input("Date", value=date.today(), key="sec_meet_date", format="DD/MM/YYYY", label_visibility="collapsed")
        d_c2.text_input("Time", value="10:00 AM", key="sec_meet_time", label_visibility="collapsed", placeholder="e.g. 10:00 AM")

    # Relay Directors
    num_dirs = st.session_state.get("num_directors", 1)
    dir_list = [st.session_state.get(f"d_name_{i}", "") for i in range(num_dirs) if st.session_state.get(f"d_name_{i}", "")]
    row_input("Directors Present", ", ".join(dir_list), "sec_dirs_present")

    st.markdown("---")

    # 2. CHAIRMAN
    st.write("#### 1. CHAIRMAN")
    default_chair = dir_list[0] if dir_list else ""
    row_input("The Chair was taken by", default_chair, "sec_chairman_name")

    # 3. INCORPORATION
    st.write("#### 2. INCORPORATION")
    st.write("It was noted that the Company was incorporated under the COMPANIES ACT.(CAP.50).")
    
    uen_number = st.session_state.get("kyc_co_no", "")
    inc_date = st.session_state.get("kyc_inc_date", date.today())

    row_input("The Certificate of Incorporation number was:", uen_number, "sec_inc_no")
    
    ci1, ci2 = st.columns([1, 3])
    with ci1: st.markdown("**The Date of Incorporation was:**")
    # DATE FORMAT FIX: Added format="DD/MM/YYYY"
    with ci2: st.date_input("Inc Date", value=inc_date, key="sec_inc_date_display", disabled=True, format="DD/MM/YYYY", label_visibility="collapsed")

    # 4. DIRECTORS
    st.write("#### 3. DIRECTORS")
    st.write("It was resolved that the following be appointed as the first director(s) of the Company:")
    for i, d_name in enumerate(dir_list):
        row_input(f"Director {i+1}", d_name, f"sec_dir_name_{i}", disabled=True)

    # 5. SHARE CAPITAL
    st.write("#### 4. SHARE CAPITAL")
    cap_amt = st.session_state.get("cap_amount", "100")
    sc1, sc2, sc3, sc4 = st.columns([2, 1, 1, 2])
    with sc1: st.write("Share capital of the Company was")
    with sc2: st.text_input("Cap Amt", value=cap_amt, key="sec_cap_amt", label_visibility="collapsed")
    with sc3: st.write("divided into")
    with sc4: st.write(f"{cap_amt} shares of 1 each.")

    # 6. ALLOTMENT
    st.write(f"#### 5. APPLICATION FOR ALLOTMENT OF {client_name.upper()}")
    st.write("The application(s) for shares in the Company were submitted. It was resolved that the application(s) be approved.")
    
    st.markdown("**Application for and allotment of shares**")
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

    # 7. REGISTERED OFFICE
    st.write("#### 6. REGISTERED OFFICE AND CORRESPONDENCE ADDRESS")
    reg_addr = st.session_state.get("reg_office_address", "")
    st.markdown("**It was resolved that the registered office of the company be situated at:**")
    st.text_input("Reg Office", value=reg_addr, key="sec_reg_office", label_visibility="collapsed")
    st.markdown("**It was resolved that the address to be used for all correspondence be as follows:**")
    st.text_input("Corr Office", value=reg_addr, key="sec_corr_office", label_visibility="collapsed")

    st.divider()

    # BUTTONS
    b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
    if b_col1.button("← Back to KYC"):
        st.session_state.view = "kyc_form"
        st.rerun()

    if b_col2.button("Generate Minutes PDF"):
        save_client_data(client_name)
        pdf_data = create_minutes_pdf(client_name)
        st.download_button("Download Minutes PDF", data=pdf_data, file_name=f"{client_name}_Minutes.pdf", mime="application/pdf")

    if b_col3.button("Next: Acceptance Form →"):
        save_client_data(client_name)
        st.session_state.view = "acceptance_form"
        st.rerun()
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

        # --- DATA FETCHING & TYPE CASTING ---
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
            
            # Use dataframe as requested
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

                    # --- ADDED KYC BUTTON HERE ---
                    if btn_col3.button("📂 Open KYC Form"):
                        st.session_state["selected_client_name"] = client_info['NAME']
                        st.session_state["view"] = "kyc_form"
                        st.rerun()
            else:
                st.info("No clients match your search.")
        else:
            st.info("No clients found.")

    # --- VIEWS FOR KYC FORM ---
    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])

    elif st.session_state["view"] == "bg_sec_file":
        bg_sec_file_form(st.session_state["selected_client_name"])