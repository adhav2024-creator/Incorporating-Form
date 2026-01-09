import streamlit as st
import pandas as pd
from database import init_db, get_clients, add_client, delete_client, update_client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Audit & Incorporation Portal", layout="wide")
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
    st.title("🔒 Corporate Secure Login")
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
    if st.button("⬅️ Back to Client Database"):
        st.session_state["view"] = "management"
        st.rerun()
    
    # --- IMAGE REFERENCE: PROGRESS TRACKER ---
    # Creating the green progress bar look from your photo
    st.markdown("""
        <style>
        .step-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .step { text-align: center; font-family: sans-serif; font-size: 14px; color: #2e7d32; }
        .circle { height: 40px; width: 40px; background-color: #2e7d32; border-radius: 50%; 
                  display: inline-flex; align-items: center; justify-content: center; color: white; 
                  font-weight: bold; margin-bottom: 5px; border: 2px solid #2e7d32; }
        .circle-inactive { background-color: white; color: #2e7d32; }
        .line { flex-grow: 1; height: 4px; background-color: #2e7d32; margin-top: -25px; }
        </style>
        <div class='step-container'>
            <div class='step'><div class='circle'>1</div><br>Master KYC Form</div>
            <div class='line'></div>
            <div class='step'><div class='circle circle-inactive'>2</div><br>BG Sec File</div>
            <div class='line'></div>
            <div class='step'><div class='circle circle-inactive'>3</div><br>Customer Acceptance Form</div>
            <div class='line'></div>
            <div class='step'><div class='circle circle-inactive'>4</div><br>Secretarial Engagement Letter</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### BASIC INFORMATION REQUEST FORM & KYC")
    
    with st.form("kyc_form_from_photo"):
        # Section A: Basic Info (Matching the photo layout)
        st.write("#### BASIC INFORMATION REQUEST FORM & KYC")
        
        # Date Field
        st.date_input("Date", value=date.today())
        st.divider()

        # Company Details Row
        st.write("**Company Details**")
        st.text_input("Company Name", value=client_name)
        
        col_id1, col_id2, col_id3 = st.columns([2, 1, 1])
        with col_id1:
            st.text_input("Company No.")
        with col_id2:
            st.text_input("Date of incorporation", placeholder="DD/MM/YYYY")
        with col_id3:
            st.text_input("Year End Date", value="31 Dec")

        st.divider()

        # Proposed Activity Row
        st.write("**Proposed Company Activity**")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.text_input("Main Activity", placeholder="e.g. Accounting, Audits")
        with col_act2:
            st.text_input("Secondary Activity", placeholder="e.g. Tax")

        st.divider()

        # Section B: Directors (From bottom of photo)
        st.write("#### DIRECTORS DETAILS")
        num_dir = st.number_input("Number of Directors", 1, 10, 1)
        
        for i in range(int(num_dir)):
            with st.container(border=True):
                r1c1, r1c2, r1c3, r1c4 = st.columns([2, 1, 1, 1])
                with r1c1: st.text_input("Name as per Passport/NRIC", key=f"dname_{i}")
                with r1c2: st.text_input("NRIC/Passport No.", key=f"did_{i}")
                with r1c3: st.text_input("Date of Birth", key=f"ddob_{i}")
                with r1c4: st.text_input("Email Address", key=f"dmail_{i}")

        if st.form_submit_button("Save Section 1"):
            st.success("Section 1 Saved Successfully")
# --- 4. MAIN APP ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("Client Management System")
        df = get_clients()

        # --- SIDEBAR: ADD NEW CLIENT ---
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
            # ORIGINAL DASHBOARD METRICS
            # 1. Ensure numeric sorting for metrics
            df['client_num'] = pd.to_numeric(df['client_num'], errors='coerce')
            
            # 2. Capitalize Headers for calculation
            df.columns = [col.replace('_', ' ').upper() for col in df.columns]

            st.subheader("📊 Practice Overview")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Total Clients", len(df))
            m_col2.metric("Active Portfolios", len(df[df['STATUS'] == 'Active']))
            m_col3.metric("Terminated", len(df[df['STATUS'] == 'Terminated']))

            st.divider()

            # --- SEARCH & INTERACTIVE TABLE ---
            st.subheader("📋 Client Database")
            search_query = st.text_input("🔍 Search by Client Name or UEN", "")
            
            # Filter Logic
            filtered_df = df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['NAME'].str.contains(search_query.upper(), na=False) | 
                    filtered_df['UEN'].str.contains(search_query.upper(), na=False)
                ]

            # Add "NEW FORM" interaction column
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

            # Check if checkbox clicked
            clicked_rows = edited_df[edited_df["NEW FORM"] == True]
            if not clicked_rows.empty:
                st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()

            st.divider()

            # --- ORIGINAL EDIT / DELETE SECTION ---
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
                        curr_month = str(client_info['YEAR END'])
                        m_idx = MONTHS.index(curr_month) if curr_month in MONTHS else 0
                        edit_month = st.selectbox("Year End", MONTHS, index=m_idx)
                        
                        stat_list = ["Active", "Terminated"]
                        curr_stat = str(client_info['STATUS'])
                        s_idx = stat_list.index(curr_stat) if curr_stat in stat_list else 0
                        edit_status = st.selectbox("Client Status", stat_list, index=s_idx)

                    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
                    if btn_col1.button("✅ Update Details", type="primary"):
                        update_client(int(selected_id), edit_num, edit_name, edit_uen, edit_month, edit_status)
                        st.success("Updated!")
                        st.rerun()
                        
                    if btn_col2.button("🗑️ Delete Client"):
                        delete_client(int(selected_id))
                        st.warning("Deleted.")
                        st.rerun()
        else:
            st.info("No clients found.")

    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])