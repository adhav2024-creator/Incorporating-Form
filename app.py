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
    # Initialize director count in session state if not already there
    if "num_directors" not in st.session_state:
        st.session_state.num_directors = 1

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

    # The main form
    with st.form("kyc_form_exact"):
        st.write("### BASIC INFORMATION REQUEST FORM AND KYC")
        st.date_input("Date", value=date(2020, 1, 1))
        
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

        # --- DIRECTORS DETAILS HEADER WITH ADD BUTTON ---
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            st.write("### DIRECTORS DETAILS")
        
        # NOTE: Form submit buttons inside forms don't rerun immediately for logic changes, 
        # but we can use a small trick by defining the number of fields based on state.
        # To make "Add" work perfectly, we use the session state value.
        
        for i in range(st.session_state.num_directors):
            st.markdown(f"#### Director {i+1} Particulars")
            
            d_col1, d_col2, d_col3 = st.columns([2, 1, 1])
            with d_col1:
                st.text_input(f"Name as per Passport/NRIC (Dir {i+1})", key=f"d_name_{i}")
            with d_col2:
                st.text_input(f"NRIC/Passport no. (Dir {i+1})", key=f"d_id_{i}")
            with d_col3:
                st.date_input(f"Date of birth (Dir {i+1})", value=date(1990, 1, 1), key=f"d_dob_{i}")
            
            d_col4, d_col5, d_col6 = st.columns([2, 1, 1])
            with d_col4:
                st.text_input(f"Email address (Dir {i+1})", key=f"d_email_{i}")
            with d_col5:
                st.text_input(f"Mobile number (Dir {i+1})", key=f"d_mobile_{i}")
            with d_col6:
                st.text_input(f"Nationality (Dir {i+1})", key=f"d_nat_{i}")
            
            st.text_area(f"Address (Dir {i+1})", key=f"d_address_{i}", height=70)
            st.write("---")

        # Submission and Increment logic
        btn_col1, btn_col2 = st.columns([1, 4])
        # We use form submit buttons for both to satisfy Streamlit requirements
        add_clicked = btn_col1.form_submit_button("+ Add Director")
        save_clicked = btn_col2.form_submit_button("Save Form")

        if add_clicked:
            st.session_state.num_directors += 1
            st.rerun()

        if save_clicked:
            st.success(f"Successfully saved details for {st.session_state.num_directors} director(s).")
# --- 4. MAIN APP ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("Client Management System")
        df = get_clients()

        st.sidebar.header("Add New Client")
        with st.sidebar.form("add_form", clear_on_submit=True):
            new_num = st.number_input("Client Number", min_value=1, step=1)
            new_name = st.text_input("Name of Customer")
            new_uen = st.text_input("UEN Number")
            new_month = st.selectbox("Year End Month", MONTHS)
            new_status = st.selectbox("Status", ["Active", "Terminated"])
            if st.form_submit_button("Save New Client"):
                if new_name:
                    add_client(new_num, new_name, new_uen, new_month, new_status)
                    st.rerun()

        if not df.empty:
            df['client_num'] = pd.to_numeric(df['client_num'], errors='coerce')
            df.columns = [col.replace('_', ' ').upper() for col in df.columns]

            st.subheader("Practice Overview")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Total Clients", len(df))
            m_col2.metric("Active Portfolios", len(df[df['STATUS'] == 'Active']))
            m_col3.metric("Terminated", len(df[df['STATUS'] == 'Terminated']))

            st.divider()

            st.subheader("Client Database")
            search_query = st.text_input("Search by Client Name or UEN", "")
            
            filtered_df = df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['NAME'].str.contains(search_query.upper(), na=False) | 
                    filtered_df['UEN'].str.contains(search_query.upper(), na=False)
                ]

            filtered_df["NEW FORM"] = False
            cols = ["NEW FORM"] + [c for c in filtered_df.columns if c != "NEW FORM"]
            display_df = filtered_df[cols]

            edited_df = st.data_editor(
                display_df,
                hide_index=True,
                use_container_width=True,
                disabled=[c for c in display_df.columns if c != "NEW FORM"],
                key="main_table"
            )

            clicked_rows = edited_df[edited_df["NEW FORM"] == True]
            if not clicked_rows.empty:
                st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()

            st.divider()

            st.subheader("Edit or Delete Client Details")
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
                        curr_month = str(client_info['YEAR END'])
                        m_idx = MONTHS.index(curr_month) if curr_month in MONTHS else 0
                        edit_month = st.selectbox("Year End", MONTHS, index=m_idx)
                        
                        stat_list = ["Active", "Terminated"]
                        curr_stat = str(client_info['STATUS'])
                        s_idx = stat_list.index(curr_stat) if curr_stat in stat_list else 0
                        edit_status = st.selectbox("Client Status", stat_list, index=s_idx)

                    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
                    if btn_col1.button("Update Details", type="primary"):
                        update_client(int(selected_id), edit_num, edit_name, edit_uen, edit_month, edit_status)
                        st.success("Updated!")
                        st.rerun()
                        
                    if btn_col2.button("Delete Client"):
                        delete_client(int(selected_id))
                        st.warning("Deleted.")
                        st.rerun()
        else:
            st.info("No clients found.")

    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])