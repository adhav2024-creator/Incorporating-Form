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

    # --- PROGRESS BAR ---
    st.markdown("""
        <style>
        .progress-container { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 20px 0; position: relative; }
        .progress-line { position: absolute; top: 45px; left: 5%; right: 5%; height: 4px; background-color: #2E7D32; z-index: 1; }
        .step { text-align: center; z-index: 2; flex: 1; }
        .circle { width: 50px; height: 50px; background-color: #2E7D32; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-weight: bold; font-size: 20px; border: 3px solid #2E7D32; }
        .inactive-circle { background-color: white; color: #2E7D32; }
        .label { margin-top: 10px; font-weight: bold; font-size: 14px; color: #2E7D32; }
        </style>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step"><div class="circle">1</div><div class="label">Master KYC Form</div></div>
            <div class="step"><div class="circle inactive-circle">2</div><div class="label">BG Sec File</div></div>
            <div class="step"><div class="circle inactive-circle">3</div><div class="label">Customer Acceptance Form</div></div>
            <div class="step"><div class="circle inactive-circle">4</div><div class="label">Secretarial Engagement Letter</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.title("BASIC INFORMATION REQUEST FORM AND KYC")

    with st.form("kyc_form_exact"):
        st.write("### BASIC INFORMATION REQUEST FORM AND KYC")
        st.date_input("Date", value=date.today())
        
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
            with d_c3: st.date_input(f"Date of birth", value=date(1990, 1, 1), key=f"d_dob_{i}")
            
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
            with s_c3: st.date_input(f"Date of Birth", value=date(1990, 1, 1), key=f"s_dob_{j}")
            
            s_c4, s_c5, s_c6 = st.columns([2, 1, 1])
            with s_c4: st.text_input(f"Email address", key=f"s_email_{j}")
            with s_c5: st.text_input(f"Mobile Number", key=f"s_mobile_{j}")
            with s_c6: st.text_input(f"Nationality", key=f"s_nat_{j}")
            st.text_area(f"Address", key=f"s_address_{j}", height=70)
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

        # --- CURRENT EMPLOYMENT/BUSINESS PARTICULARS ---
        st.write("### CURRENT EMPLOYMENT/BUSINESS PARTICULARS")
        emp_c1, emp_c2 = st.columns(2)
        with emp_c1:
            st.text_input("BO's Name", key="emp_bo_name")
            st.text_input("Company Name", key="emp_company")
            st.text_input("Business Nature/Industry", key="emp_industry")
        with emp_c2:
            st.text_input("Years in employment", key="emp_years_employment")
            st.text_input("Years of experience in the industry", key="emp_years_exp")
            st.file_uploader("Addition of CV", type=["pdf", "doc", "docx"], key="emp_cv")

        st.divider()

        # --- BO'S SOURCE OF WEALTH ---
        st.write("### BO'S SOURCE OF WEALTH")
        sow_options = [
            ("Salary/Bonus Income (Annual) Name of the employer, position and annual salary", "salary"),
            ("Owner of Shares in Business Name of the company, website, annual salary", "shares"),
            ("Inheritance or Gift Name of the deceased/donor, type of business/investment, relationship, amount received", "inheritance"),
            ("Investment Name of the investment manager, value of portfolio, origin of investment funds", "investment"),
            ("Sale of Assets/Shares Type of assets/shares, date of sale, value of sale", "sale"),
            ("Others (Please provide details )", "others")
        ]

        for label, key in sow_options:
            c1, c2 = st.columns([2, 1])
            with c1: st.checkbox(label, key=f"sow_check_{key}")
            with c2: st.text_area("Details", key=f"sow_text_{key}", height=68, label_visibility="collapsed")

        st.divider()

        # --- DECLARATION/UNDERTAKING ---
        st.write("### DECLARATION/UNDERTAKING")
        st.info("""
        1. I/We confirm information is true and accurate.
        2. I/We understand the legal and tax reporting requirements and will comply with all relevant reporting requirements.
        3. I/we understand that all documents supplied will not be returned.
        4. I/we undertake to notify of any future changes to the information.
        """)
        
        # --- SIGNATURE SECTION ---
        st.write("### SIGNATURE OF BENEFICIAL OWNER")
        st.text_input("Full Name of the Beneficial Owner", key="decl_bo_name")
        
        st.write("Upload Signature (Image from Dropbox or Local)")
        signature_file = st.file_uploader("Upload PNG/JPG Signature", type=["png", "jpg", "jpeg"], key="sig_upload")
        if signature_file:
            st.image(signature_file, width=300, caption="Beneficial Owner Signature Preview")

        st.divider()
        
        # --- SUBMISSION BUTTONS ---
        btn_col1, _, btn_col3 = st.columns([1, 4, 1])
        with btn_col1:
            if st.form_submit_button("SAVE AS DRAFT"):
                st.info("Form saved as draft.")
        with btn_col3:
            if st.form_submit_button("SUBMIT NOW"):
                st.success("Master KYC Submitted Successfully")

# --- 4. MAIN APP LOGIC ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("🏢 Client Management System")

        # --- 2. DATA FETCHING ---
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

        # --- 3. SIDEBAR (ADD CLIENT) ---
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

        # --- 4. MAIN DISPLAY & FORM ACCESS ---
        if not df.empty:
            st.subheader("📋 Client Database")
            st.info("💡 Check the **'ENTER FORM'** box next to a client to open their KYC form.")
            
            search_query = st.text_input("🔍 Search by Client Name or UEN", "")
            
            filtered_df = df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['NAME'].str.contains(search_query, case=False, na=False) | 
                    filtered_df['UEN'].str.contains(search_query, case=False, na=False)
                ]

            # Adding interactive column for form access
            filtered_df.insert(0, "ENTER FORM", False)
            
            # Use data_editor to allow clicking the "ENTER FORM" checkbox
            edited_df = st.data_editor(
                filtered_df,
                hide_index=True,
                use_container_width=True,
                disabled=[c for c in filtered_df.columns if c != "ENTER FORM"], # Only allow checkbox to be clicked
                key="main_table"
            )

            # Check if a checkbox was clicked
            clicked_rows = edited_df[edited_df["ENTER FORM"] == True]
            if not clicked_rows.empty:
                st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()

            st.divider()

            # --- 5. EDIT / DELETE SECTION ---
            st.subheader("📝 Edit or Delete Client Details")
            client_options = {f"{row['NAME']} (ID: {row['ID']})": row['ID'] for _, row in filtered_df.iterrows()}
            
            if client_options:
                selected_option = st.selectbox("Select a client to modify:", list(client_options.keys()))
                selected_id = client_options[selected_option]
                client_info = df[df['ID'] == selected_id].iloc[0]
                
                with st.expander(f"Modify Details for {client_info['NAME']}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_num = st.number_input("Client Number", value=int(client_info['CLIENT NUM']), key="edit_num")
                        edit_name = st.text_input("Customer Name", value=str(client_info['NAME']), key="edit_name")
                        edit_uen = st.text_input("UEN", value=str(client_info['UEN']), key="edit_uen")
                    with col2:
                        current_month = str(client_info['YEAR END'])
                        month_idx = MONTHS.index(current_month) if current_month in MONTHS else 0
                        edit_month = st.selectbox("Year End", MONTHS, index=month_idx, key="edit_month")
                        edit_status = st.selectbox("Client Status", ["Active", "Terminated"], 
                                                 index=0 if client_info['STATUS'] == "Active" else 1, key="edit_status")

                    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
                    if btn_col1.button("✅ Update Details", type="primary"):
                        update_client(int(client_info['ID']), edit_num, edit_name, edit_uen, edit_month, edit_status)
                        st.success("Updated!")
                        st.rerun()
                        
                    if btn_col2.button("🗑️ Delete Client"):
                        delete_client(int(client_info['ID']))
                        st.warning("Deleted.")
                        st.rerun()
        else:
            st.info("No clients found.")

    elif st.session_state["view"] == "kyc_form":
        # Calls the function defined in your Step 3
        master_kyc_form(st.session_state["selected_client_name"])