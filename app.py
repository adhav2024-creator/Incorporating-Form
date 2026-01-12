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

    # --- PROGRESS BAR (5 Steps) ---
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

    with st.form("kyc_main_form"):
        st.write("### BASIC INFORMATION REQUEST FORM AND KYC")
        st.date_input("Date", value=date.today(), key="main_form_date")
        
        # --- COMPANY DETAILS ---
        st.write("### Company Details")
        st.text_input("Company Name", value=client_name, key="kyc_comp_name")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1: st.text_input("Company No.", value="200517609N", key="kyc_comp_no")
        with col2: st.date_input("Date of incorporation", value=date(2005, 1, 1), key="kyc_incorp_date")
        with col3: st.text_input("Year End Date", value="31 Dec", key="kyc_year_end")

        st.write("#### Proposed Company Activity")
        act_col1, act_col2 = st.columns(2)
        with act_col1: st.text_input("Main Activity", value="Accounting, Audits", key="kyc_main_act")
        with act_col2: st.text_input("Secondary Activity", value="Tax", key="kyc_sec_act")

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
            with d_c1: st.text_input(f"Name (Passport/NRIC)", key=f"d_name_{i}")
            with d_c2: st.text_input(f"NRIC/Passport no.", key=f"d_id_{i}")
            with d_c3: st.date_input(f"Date of birth", key=f"d_dob_{i}")
            st.text_area(f"Address", key=f"d_address_{i}", height=70)

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
            s_c1, s_c2 = st.columns([2, 2])
            with s_c1: 
                name = st.text_input(f"Name", key=f"s_name_{j}")
                sh_names.append(name if name else f"Shareholder {j+1}")
            with s_c2: st.text_input(f"NRIC/Passport", key=f"s_id_{j}")
            st.text_area(f"Address", key=f"s_address_{j}", height=70)

        st.divider()

        # --- PERCENTAGE OF SHAREHOLDING ---
        st.write("### PERCENTAGE OF SHAREHOLDING DETAILS")
        for k in range(st.session_state.num_shareholders):
            st.write(f"#### {sh_names[k]}")
            p_c1, p_c2 = st.columns(2)
            with p_c1:
                st.text_input(f"Share %", key=f"p_perc_{k}")
                st.text_input(f"Shares Applied", key=f"p_applied_{k}")
            with p_c2:
                st.text_input(f"Shares Issued", key=f"p_issued_{k}")
                st.text_input(f"Paid up amount", key=f"p_paid_{k}")

        st.divider()

        # --- OFFICE & CONTACT ---
        st.write("### REGISTERED OFFICE AND SECRETARIAL RECORDS")
        reg_c1, reg_c2 = st.columns(2)
        with reg_c1: st.text_area("Registered Office Address", key="reg_office_addr", height=80)
        with reg_c2: st.text_area("Secretarial Records Address", key="sec_records_addr", height=80)

        st.write("### AUTHORISED PERSON TO CONTACT")
        auth_c1, auth_c2, auth_c3 = st.columns([2, 1, 1])
        with auth_c1: st.text_input("Name", key="auth_contact_name")
        with auth_c2: st.text_input("Mobile", key="auth_contact_mobile")
        with auth_c3: st.text_input("Email", key="auth_contact_email")

        st.write("### BANK ACCOUNT")
        bank_c1, bank_c2 = st.columns(2)
        with bank_c1: st.text_input("Preferred Bank Name", key="bk_name")
        with bank_c2: st.text_input("Currency of Account", key="bk_currency")

        st.write("### CORRESPONDENCE ADDRESS")
        st.text_area("Correspondence Address", key="correspond_addr", height=80)

        st.divider()

        # --- EMPLOYMENT & SOURCE OF WEALTH ---
        st.write("### CURRENT EMPLOYMENT/BUSINESS PARTICULARS")
        emp_c1, emp_c2 = st.columns(2)
        with emp_c1:
            st.text_input("BO's Name", key="emp_bo_name")
            st.text_input("Company Name", key="emp_co_name")
            st.text_input("Business Nature/Industry", key="emp_industry")
        with emp_c2:
            st.text_input("Years in employment", key="emp_years")
            st.text_input("Years of experience in industry", key="emp_exp")
            st.file_uploader("Addition of CV", type=["pdf", "doc", "docx"], key="emp_cv_upload")

        st.divider()
        st.write("### BO'S SOURCE OF WEALTH")
        sow_items = [
            ("Salary/Bonus Income (Annual) Name of the employer, position and annual salary", "salary"),
            ("Owner of Shares in Business Name of the company, website, annual salary", "shares"),
            ("Inheritance or Gift Name of the deceased/donor, type of business/investment, relationship, amount received", "inheritance"),
            ("Investment Name of the investment manager, value of portfolio, origin of investment funds", "invest"),
            ("Sale of Assets/Shares Type of assets/shares, date of sale, value of sale", "sale_assets"),
            ("Others (Please provide details )", "others_wealth")
        ]
        for label, k in sow_items:
            c1, c2 = st.columns([2, 3])
            with c1: st.checkbox(label, key=f"sow_chk_{k}")
            with c2: st.text_area("Details", key=f"sow_det_{k}", height=80, label_visibility="collapsed")

        st.divider()

        # --- DECLARATION & SIGNATURE ---
        st.write("### DECLARATION/UNDERTAKING")
        st.info("""1. I/We confirm that the above information is true and accurate...
2. I/We understand the legal and tax reporting requirements...
3. I/We understand and agree that all documents supplied will not be returned...
4. I/We undertake to notify us of any future changes...
5. I/We understand the right to request additional documentation.""")
        
        st.write("**Name of the Beneficial Owner**")
        st.text_input("BO Name", value="Janakiraman Ayyappan", key="final_decl_name", label_visibility="collapsed")

        st.write("### SIGNATURE")
        st.write("__________________________________________")
        st.caption("Signature")

        st.write("")
        b_col1, b_col2, b_col3 = st.columns([1, 4, 1])
        with b_col1: st.form_submit_button("SAVE AS DRAFT", key="btn_save_draft")
        with b_col3: 
            if st.form_submit_button("SUBMIT NOW", key="btn_submit_final"):
                st.success("Master KYC Submitted Successfully")

# --- 4. MAIN APP LOGIC ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("Client Management System")
        df = get_clients()
        
        # Sidebar for new client
        with st.sidebar.form("add_client_form"):
            st.header("Add New Client")
            n_num = st.number_input("No.", min_value=1)
            n_name = st.text_input("Customer Name")
            n_uen = st.text_input("UEN")
            n_mon = st.selectbox("Year End", MONTHS)
            n_stat = st.selectbox("Status", ["Active", "Terminated"])
            if st.form_submit_button("Add Client"):
                add_client(n_num, n_name, n_uen, n_mon, n_stat)
                st.rerun()

        if not df.empty:
            df.columns = [col.upper() for col in df.columns]
            df["NEW FORM"] = False
            cols = ["NEW FORM"] + [c for c in df.columns if c != "NEW FORM"]
            edited_df = st.data_editor(df[cols], hide_index=True, use_container_width=True, key="client_table")
            
            clicked = edited_df[edited_df["NEW FORM"] == True]
            if not clicked.empty:
                st.session_state["selected_client_name"] = clicked.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()
    
    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])