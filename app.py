import streamlit as st
import pandas as pd
from database import init_db, get_clients, add_client, delete_client, update_client
from datetime import date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Audit and Incorporation Portal", layout="wide")
init_db()

MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# --- 2. STATE MANAGEMENT ---
if "view" not in st.session_state:
    st.session_state["view"] = "management"
if "selected_client_name" not in st.session_state:
    st.session_state["selected_client_name"] = None
if "num_directors" not in st.session_state:
    st.session_state.num_directors = 1
if "num_shareholders" not in st.session_state:
    st.session_state.num_shareholders = 1

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.title("Corporate Secure Login")
    password = st.text_input("Enter Office Password", type="password")
    if st.button("Login"):
        if password == "Awesome2050@": 
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False

# --- 3. KYC FORM SECTION ---
def master_kyc_form(client_name):
    if st.button("Back to Client Database"):
        st.session_state["view"] = "management"
        st.rerun()

    # --- PROGRESS BAR (Updated to 5 Steps) ---
    st.markdown("""
        <style>
        .progress-container { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 20px 0; position: relative; }
        .progress-line { position: absolute; top: 45px; left: 5%; right: 5%; height: 4px; background-color: #2E7D32; z-index: 1; }
        .step { text-align: center; z-index: 2; flex: 1; }
        .circle { width: 50px; height: 50px; background-color: #2E7D32; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-weight: bold; font-size: 20px; border: 3px solid #2E7D32; }
        .inactive-circle { background-color: white; color: #2E7D32; }
        .label { margin-top: 10px; font-weight: bold; font-size: 13px; color: #2E7D32; }
        </style>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step"><div class="circle">1</div><div class="label">Master KYC Form</div></div>
            <div class="step"><div class="circle inactive-circle">2</div><div class="label">BG Sec File</div></div>
            <div class="step"><div class="circle inactive-circle">3</div><div class="label">Customer Acceptance Form</div></div>
            <div class="step"><div class="circle inactive-circle">4</div><div class="label">Secretarial Engagement Letter</div></div>
            <div class="step"><div class="circle inactive-circle">5</div><div class="label">Terms and Conditions</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.title("BASIC INFORMATION REQUEST FORM AND KYC")

    with st.form("kyc_form_exact"):
        st.date_input("Date", value=date(2020, 1, 1))
        
        # --- COMPANY DETAILS ---
        st.write("### Company Details")
        st.text_input("Company Name", value=client_name)
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1: st.text_input("Company No.", value="200517609N")
        with col2: st.date_input("Date of incorporation", value=date(2005, 1, 1))
        with col3: st.text_input("Year End Date", value="31 Dec")
        st.write("#### Proposed Company Activity")
        act_col1, act_col2 = st.columns(2)
        with act_col1: st.text_input("Main Activity", value="Accounting, Audits")
        with act_col2: st.text_input("Secondary Activity", value="Tax")

        st.divider()

        # --- DIRECTORS ---
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
            with d_c1: st.text_input(f"Name (Passport/NRIC)", key=f"d_name_{i}")
            with d_c2: st.text_input(f"NRIC/Passport no.", key=f"d_id_{i}")
            with d_c3: st.date_input(f"DOB", key=f"d_dob_{i}")
            st.text_area(f"Address", key=f"d_address_{i}", height=70)

        st.divider()

        # --- SHAREHOLDERS ---
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
            st.markdown(f"#### Shareholder {j+1}")
            s_c1, s_c2 = st.columns([2, 2])
            with s_c1: 
                name = st.text_input(f"Name", key=f"s_name_{j}")
                sh_names.append(name if name else f"Shareholder {j+1}")
            with s_c2: st.text_input(f"NRIC/Passport", key=f"s_id_{j}")
            st.text_area(f"Address", key=f"s_address_{j}", height=70)

        st.divider()

        # --- AUTHORISED PERSON / OFFICE / BANK ---
        st.write("### AUTHORISED PERSON TO CONTACT")
        auth_c1, auth_c2, auth_c3 = st.columns([2, 1, 1])
        with auth_c1: st.text_input("Name", key="auth_name")
        with auth_c2: st.text_input("Mobile", key="auth_mobile")
        with auth_c3: st.text_input("Email", key="auth_email")

        st.write("#### REGISTERED OFFICE")
        st.text_area("Registered Office Address", key="reg_office_address", height=80)

        st.write("#### BANK ACCOUNT")
        bank_c1, bank_c2 = st.columns(2)
        with bank_c1: st.text_input("Preferred Bank", key="bank_name")
        with bank_c2: st.text_input("Account Currency", key="bank_account_currency")

        st.divider()

        # --- EMPLOYMENT PARTICULARS ---
        st.write("### CURRENT EMPLOYMENT/BUSINESS PARTICULARS")
        emp_c1, emp_c2 = st.columns(2)
        with emp_c1:
            st.text_input("BO's Name", key="emp_bo_name")
            st.text_input("Company Name", key="emp_company")
            st.text_input("Business Nature", key="emp_industry")
        with emp_c2:
            st.text_input("Years in employment", key="emp_years_employment")
            st.text_input("Years in industry", key="emp_years_exp")
            st.file_uploader("Upload CV", type=["pdf", "doc", "docx"], key="emp_cv")

        st.divider()

        # --- BO'S SOURCE OF WEALTH (As per Image) ---
        st.write("### BO'S SOURCE OF WEALTH")

        sow_fields = [
            ("Salary/Bonus Income (Annual) Name of the employer, position and annual salary", "sow_salary"),
            ("Owner of Shares in Business Name of the company, website, annual salary", "sow_shares"),
            ("Inheritance or Gift Name of the deceased/donor, type of business/investment, relationship, amount received", "sow_gift"),
            ("Investment Name of the investment manager, value of portfolio, origin of investment funds", "sow_inv"),
            ("Sale of Assets/Shares Type of assets/shares, date of sale, value of sale", "sow_sale"),
            ("Others (Please provide details )", "sow_other")
        ]

        for label, key_prefix in sow_fields:
            col_check, col_text = st.columns([2, 3])
            with col_check:
                st.checkbox(label, key=f"{key_prefix}_check")
            with col_text:
                st.text_area("Details", key=f"{key_prefix}_details", height=80, label_visibility="collapsed")

        if st.form_submit_button("SUBMIT NOW"):
            st.success("Master KYC Form Saved Successfully")
        st.divider()

        # --- DECLARATION/UNDERTAKING ---
        st.write("### DECLARATION/UNDERTAKING")
        declaration_text = """
        1. I/We confirm that the above information is true and accurate, and hereby authorise to supply any or all of such information for due diligence purpose to the Regulators if so requested by them without notification to you.
        2. I/We understand the legal and tax reporting requirements and other responsibilities in my/our country of residence and/or other applicable jurisdictions and will company with all the elevant reporting requirements of my /our own. We strongly suggest to seek independent tax advice from a third party tax professional not associated with our company with respect the incorporation or investments.
        3. I/We understand and agree that all documents supplied including this form will not be returned to me/us.
        4. I/We also undertake to notify us of any future changes to the above information.
        5. I/We understand and that we reserves the right to request for additional documentation/information.
        """
        st.info(declaration_text)
        
        st.write("**Name of the Beneficial Owner**")
        st.text_input("Beneficial Owner Name", value="Janakiraman Ayyappan", key="decl_bo_name", label_visibility="collapsed")

        st.divider()

        # --- SIGNATURE SECTION ---
        st.write("### SIGNATURE")
        sig_col1, sig_col2 = st.columns(2)
        with sig_col1:
            st.write("__________________________________________")
            st.caption("Signature")
        
        # Bottom Buttons
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        with btn_col1:
            st.form_submit_button("SAVE AS DRAFT")
        with btn_col3:
            if st.form_submit_button("SUBMIT NOW"):
                st.success("Form Submitted Successfully")
# --- 4. MAIN APP LOGIC ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("Client Management System")
        df = get_clients()
        if not df.empty:
            df.columns = [col.upper() for col in df.columns]
            filtered_df = df.copy()
            filtered_df["NEW FORM"] = False
            cols = ["NEW FORM"] + [c for c in filtered_df.columns if c != "NEW FORM"]
            edited_df = st.data_editor(filtered_df[cols], hide_index=True, use_container_width=True, key="main_table")
            clicked_rows = edited_df[edited_df["NEW FORM"] == True]
            if not clicked_rows.empty:
                st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()
    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])