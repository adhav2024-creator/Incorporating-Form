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

# Define universal date limits to prevent the 2015 restriction
MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)

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
    
    # --- COMPANY DETAILS SECTION (TABLE FORMAT) ---
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " Company Details", ln=True, fill=True, border=1)
    
    pdf.set_font("Arial", '', 9)
    
    # Row 1: Company Name
    pdf.cell(65, 12, " Company Name", border=1)
    pdf.cell(125, 12, str(st.session_state.get('kyc_co_name', client_name)), border=1, ln=True)
    
    # Row 2: Co No & Inc Date (Stacked multi-line as per PDF)
    pdf.cell(65, 18, " Company No. & Date of incorporation", border=1)
    x = pdf.get_x()
    y = pdf.get_y()
    
    inc_date = st.session_state.get('kyc_inc_date')
    fmt_date = inc_date.strftime('%d/%m/%Y') if inc_date else ""
    uen = st.session_state.get('kyc_co_no', '')
    
    pdf.multi_cell(125, 9, f"{fmt_date}\n{uen}", border=1)
    pdf.set_xy(x + 190, y + 18) 
    pdf.ln(0)

    # Row 3: Year End Date
    pdf.cell(65, 12, " Year End Date", border=1)
    pdf.cell(125, 12, str(st.session_state.get('kyc_year_end', '')), border=1, ln=True)
    
    # Row 4: Proposed Activity
    pdf.cell(65, 20, " Proposed Company Activity", border=1)
    # Combining activity fields for the PDF
    act_main = st.session_state.get('kyc_act_main', '')
    act_sec = st.session_state.get('kyc_act_sec', '')
    full_act = f"{act_main}\n{act_sec}"
    pdf.multi_cell(125, 10, full_act, border=1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. KYC FORM SECTION ---
def master_kyc_form(client_name):
    if st.button("Back to Client Database"):
        st.session_state["view"] = "management"
        st.rerun()

    # --- PROGRESS BAR ---
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

    # START FORM
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

        st.write("#### Proposed Company Activity")
        act_col1, act_col2 = st.columns(2)
        with act_col1: st.text_input("Main Activity", value="Accounting, Audits", key="kyc_act_main")
        with act_col2: st.text_input("Secondary Activity", value="Tax", key="kyc_act_sec")

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

        # --- SHAREHOLDER DETAILS & BENEFICIAL OWNERSHIP ---
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

            st.write(f"**SIGNATURE OF BENEFICIAL OWNER - {sh_names[j]}**")
            sig_file = st.file_uploader(f"Upload Signature for {sh_names[j]}", type=["png", "jpg"], key=f"sig_{j}")
            if sig_file: st.image(sig_file, width=250)
            st.write("---")

        st.divider()

        # --- PERCENTAGE OF SHAREHOLDING DETAILS ---
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

        # --- COMPANY SECRETARY ---
        st.write("### COMPANY SECRETARY")
        sec_c1, sec_c2 = st.columns([2, 1])
        with sec_c1:
            st.text_input("Name as per passport/NRIC", key="sec_name")
            st.text_area("Address", key="sec_address", height=70)
        with sec_c2:
            st.text_input("NRIC/Passport no.", key="sec_id")
            st.text_input("Nationality", key="sec_nat")

        st.divider()

        # --- CEO DETAILS ---
        st.write("### CEO DETAILS")
        ceo_c1, ceo_c2 = st.columns([2, 1])
        with ceo_c1: st.text_input("Name as per Passport/NRIC", key="ceo_name")
        with ceo_c2: st.text_input("NRIC/Passport", key="ceo_id")
        ceo_c3, ceo_c4 = st.columns(2)
        with ceo_c3: st.text_input("Mobile Number", key="ceo_mobile")
        with ceo_c4: st.text_input("Email address", key="ceo_email")
        st.text_area("Address", key="ceo_address", height=70)

        st.divider()

        # --- AUTHORISED PERSON & SHARE CAPITAL ---
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

        # --- REGISTERED OFFICE & SECRETARIAL RECORDS ---
        st.write("### REGISTERED OFFICE AND SECRETARIAL RECORDS")
        reg_c1, reg_c2 = st.columns(2)
        with reg_c1:
            st.write("#### Registered Office")
            st.text_area("Registered Office Address", key="reg_office_address", height=100)
        with reg_c2:
            st.write("#### Secretarial Records")
            st.text_area("Secretarial Records Address", key="sec_records_address", height=100)

        st.divider()

        # --- BANK ACCOUNT ---
        st.write("### BANK ACCOUNT")
        bank_col1, bank_col2 = st.columns(2)
        with bank_col1: st.text_input("Preferred Bank Name", key="bank_name")
        with bank_col2: st.text_input("Currency of Account", key="bank_account_currency")

        st.divider()

        # --- CORRESPONDENCE ADDRESS ---
        st.write("### CORRESPONDENCE ADDRESS")
        st.text_area("Correspondence Address Details", key="correspondence_address", height=100)

        st.divider()

        # --- DECLARATION ---
        st.write("### DECLARATION/UNDERTAKING")
        st.info("""
        1. I/We confirm information is true and accurate.
        2. I/We understand the legal and tax reporting requirements.
        3. I/we understand that all documents supplied will not be returned.
        4. I/we undertake to notify of any future changes.
        """)

        # --- FORM ACTIONS ---
        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            if st.form_submit_button("SAVE AS DRAFT"):
                st.info("Form saved as draft.")
        with btn_col2:
            if st.form_submit_button("SUBMIT NOW"):
                st.session_state["view"] = "bg_sec_file"
                st.rerun()

    # --- DOWNLOAD BUTTON ---
    st.write("### Actions")
    try:
        pdf_bytes = create_pdf_report(client_name)
        st.download_button(
            label="📥 DOWNLOAD KYC PDF",
            data=pdf_bytes,
            file_name=f"KYC_{client_name}.pdf",
            mime="application/pdf",
            key="download_kyc_btn_unique"
        )
    except Exception as e:
        st.error(f"Error preparing PDF: {e}")

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
            st.date_input("Date of Meeting", value=inc_date, format="DD/MM/YYYY", min_value=MIN_DATE, max_value=MAX_DATE)
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

if st.session_state["view"] == "management":
    st.title("🏢 Client Management System")
    df = get_clients()
    if not df.empty:
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