import streamlit as st
import pandas as pd
from database import init_db, get_clients, add_client, delete_client, update_client
from datetime import date
from fpdf import FPDF

# --- 1. CONFIGURATION & DATABASE ---
st.set_page_config(page_title="Audit and Incorporation Portal", layout="wide")
init_db()

MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# --- 2. PDF GENERATOR ENGINE ---
class KYC_PDF(FPDF):
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
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "BASIC INFORMATION REQUEST FORM & KYC", ln=True, align='C')
    pdf.ln(5)

    # --- COMPANY DETAILS TABLE (MATCHING PDF FORMAT) ---
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " Company Details", ln=True, fill=True, border=1)
    
    pdf.set_font("Arial", '', 9)
    # Row 1: Company Name
    pdf.cell(65, 12, " Company Name", border=1)
    pdf.cell(125, 12, str(st.session_state.get('kyc_co_name', client_name)), border=1, ln=True)
    
    # Row 2: Company No & Inc Date (Stacked multi-line)
    pdf.cell(65, 18, " Company No. & Date of incorporation", border=1)
    curr_x, curr_y = pdf.get_x(), pdf.get_y()
    inc_date = st.session_state.get('kyc_inc_date')
    fmt_date = inc_date.strftime('%d/%m/%Y') if inc_date else ""
    uen = st.session_state.get('kyc_co_no', '')
    pdf.multi_cell(125, 9, f"{fmt_date}\n{uen}", border=1)
    pdf.set_xy(curr_x + 190, curr_y + 18)
    pdf.ln(0)

    # Row 3: Year End Date
    pdf.cell(65, 12, " Year End Date", border=1)
    pdf.cell(125, 12, str(st.session_state.get('kyc_year_end', '')), border=1, ln=True)
    
    # Row 4: Activity
    pdf.cell(65, 20, " Proposed Company Activity", border=1)
    pdf.multi_cell(125, 10, str(st.session_state.get('kyc_activity', '')), border=1)
    
    # Note: Directors and Shareholder table logic would follow here similarly...
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. KYC FORM SECTION ---
def master_kyc_form(client_name):
    if st.button("Back to Client Database"):
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
            <div class="step"><div class="circle inactive-circle">4</div><div class="label">Secretarial Engagement Letter</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.title("BASIC INFORMATION REQUEST FORM AND KYC")

    # Defined reusable date limits
    MIN_DATE = date(1900, 1, 1)
    MAX_DATE = date(2100, 12, 31)

    with st.form("kyc_form_exact"):
        st.write("### BASIC INFORMATION REQUEST FORM AND KYC")
        st.date_input("Date", value=date.today(), format="DD/MM/YYYY", min_value=MIN_DATE, max_value=MAX_DATE)
        
        # --- COMPANY DETAILS ---
        st.write("### Company Details")
        st.text_input("Company Name", value=client_name, key="kyc_co_name")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1: st.text_input("Company No.", value="200517609N", key="kyc_co_no")
        with col2: st.date_input("Date of incorporation", value=date(2005, 1, 1), format="DD/MM/YYYY", key="kyc_inc_date", min_value=MIN_DATE, max_value=MAX_DATE)
        with col3: st.text_input("Year End Date", value="31 Dec", key="kyc_year_end")

        st.text_area("Proposed Company Activity", key="kyc_activity", placeholder="Main and Secondary Activities")

        st.divider()

        # --- DIRECTORS DETAILS ---
        d_head_col, d_add_col, d_rem_col = st.columns([4, 1, 1])
        with d_head_col: st.write("### DIRECTORS DETAILS")
        
        if d_add_col.form_submit_button("+ Add Director"):
            st.session_state.num_directors += 1
            st.rerun()
        if d_rem_col.form_submit_button("- Remove Director"):
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

        # --- SHAREHOLDER DETAILS ---
        s_head_col, s_add_col, s_rem_col = st.columns([4, 1, 1])
        with s_head_col: st.write("### SHAREHOLDER DETAILS & BENEFICIAL OWNERSHIP")
        
        if s_add_col.form_submit_button("+ Add Shareholder"):
            st.session_state.num_shareholders += 1
            st.rerun()
        if s_rem_col.form_submit_button("- Remove Shareholder"):
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
            st.text_area(f"Address", key=f"s_address_{j}", height=70)
            # ... Employment and SOW sections remain same ...
            st.write("---")

        if st.form_submit_button("SUBMIT NOW"):
            st.session_state["view"] = "bg_sec_file"
            st.rerun()

    # --- ACTIONS ---
    try:
        pdf_bytes = create_pdf_report(client_name)
        st.download_button("📥 DOWNLOAD KYC PDF", data=pdf_bytes, file_name=f"KYC_{client_name}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")
# --- 4. BG SEC FILE SECTION ---
def bg_sec_file_form(client_name):
    if st.button("Back to Master KYC"):
        st.session_state["view"] = "kyc_form"
        st.rerun()

    st.markdown("""
        <style>
        .progress-container { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 20px 0; position: relative; }
        .progress-line { position: absolute; top: 45px; left: 5%; right: 5%; height: 4px; background-color: #2E7D32; z-index: 1; }
        .step { text-align: center; z-index: 2; flex: 1; }
        .circle { width: 50px; height: 50px; background-color: #2E7D32; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-weight: bold; font-size: 20px; border: 3px solid #2E7D32; }
        .active-circle { background-color: #2E7D32; color: white; }
        .completed-circle { background-color: #2E7D32; color: white; }
        .inactive-circle { background-color: white; color: #2E7D32; border: 3px solid #2E7D32; }
        .label { margin-top: 10px; font-weight: bold; font-size: 14px; color: #2E7D32; }
        </style>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step"><div class="circle completed-circle">1</div><div class="label">Master KYC Form</div></div>
            <div class="step"><div class="circle active-circle">2</div><div class="label">BG Sec File</div></div>
            <div class="step"><div class="circle inactive-circle">3</div><div class="label">Customer Acceptance Form</div></div>
            <div class="step"><div class="circle inactive-circle">4</div><div class="label">Secretarial Engagement Letter</div></div>
        </div>
        """, unsafe_allow_html=True)

    with st.form("bg_sec_file_form"):
        col_header_1, col_header_2 = st.columns([1, 1])
        with col_header_1: st.write("**FIRST DIRECTORS' MINUTES**")
        with col_header_2: st.write(f"**{client_name.upper()}**")
            
        st.divider()
        st.text_input("Name of Company", value=client_name)
        st.text_input("Place of Meeting", value="NO 10, JALAN BESAR, SIM LIM TOWER #09-03, SINGAPORE 208787")
        
        dt_col1, dt_col2 = st.columns(2)
        with dt_col1:
            inc_date = st.session_state.get("kyc_inc_date", date(2005, 1, 1))
            st.date_input("Date of Meeting", value=inc_date, format="DD/MM/YYYY")
        with dt_col2:
            st.text_input("Time of Meeting", value="13:47")

        st.write("**Directors Present**")
        default_directors = [st.session_state.get(f"d_name_{i}", "") for i in range(st.session_state.get("num_directors", 1))]
        st.text_area("Directors Present", value=", ".join([d for d in default_directors if d]), height=70, label_visibility="collapsed")

        if st.form_submit_button("SUBMIT NOW"):
            st.success("First Directors' Minutes Generated Successfully!")

# --- 5. MAIN LOGIC ---
if 'view' not in st.session_state: st.session_state["view"] = "management"
if 'num_directors' not in st.session_state: st.session_state.num_directors = 1
if 'num_shareholders' not in st.session_state: st.session_state.num_shareholders = 1

# Assuming check_password() is provided elsewhere
if st.session_state["view"] == "management":
    st.title("🏢 Client Management System")
    df = get_clients()
    if not df.empty:
        # Client database table and search...
        search_query = st.text_input("🔍 Search by Client Name or UEN", "")
        filtered_df = df.copy()
        filtered_df.insert(0, "ENTER FORM", False)
        edited_df = st.data_editor(filtered_df, hide_index=True, use_container_width=True, key="main_table")

        clicked_rows = edited_df[edited_df["ENTER FORM"] == True]
        if not clicked_rows.empty:
            st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
            st.session_state["view"] = "kyc_form"
            st.rerun()

elif st.session_state["view"] == "kyc_form":
    master_kyc_form(st.session_state["selected_client_name"])

elif st.session_state["view"] == "bg_sec_file":
    bg_sec_file_form(st.session_state["selected_client_name"])