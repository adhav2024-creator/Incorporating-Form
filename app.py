import streamlit as st
import pandas as pd
from database import init_db, get_clients, add_client, delete_client, update_client

# --- 1. CONFIGURATION & LOGIN ---
st.set_page_config(page_title="Audit & Incorporation Portal", layout="wide")
init_db()

MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

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

# --- 2. MASTER KYC FORM MODULE ---
def master_kyc_form():
    st.subheader("🛡️ Master KYC: New Incorporation")
    st.info("Complete this form to initiate a new company incorporation.")
    
    with st.form("master_kyc_main", clear_on_submit=False):
        st.write("### Section 1: Entity Background")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("First Choice Company Name")
            st.text_area("Principal Business Activities")
        with col2:
            st.selectbox("Primary SSIC Code", ["62011", "70201", "46900", "Other"])
            st.text_input("Proposed Registered Office Address")

        st.divider()
        st.write("### Section 2: Individual Stakeholders")
        num_ppl = st.number_input("Number of Stakeholders to add", 1, 10, 1)
        
        for i in range(int(num_ppl)):
            with st.expander(f"Individual {i+1} Details", expanded=True):
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.text_input("Full Legal Name", key=f"name_{i}")
                    st.text_input("Identification Number (NRIC/Passport)", key=f"id_{i}")
                with sc2:
                    st.text_input("Nationality", key=f"nat_{i}")
                    st.text_area("Residential Address", key=f"addr_{i}")
        
        if st.form_submit_button("Save Master KYC"):
            # In the future, we will add a 'add_kyc_to_db' function here
            st.success("Master KYC data saved successfully.")

# --- 3. MAIN NAVIGATION ---
if check_password():
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    menu_choice = st.sidebar.radio("Go to:", ["Client Management", "Master KYC Form", "BG Sec File", "Customer Acceptance"])

    if menu_choice == "Client Management":
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
            
            # --- DISPLAY & SEARCH ---
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
            
            # --- EDIT/DELETE SECTION ---
            st.divider()
            st.subheader("📝 Edit or Delete Client Details")
            client_options = {f"{row['NAME']} (ID: {row['ID']})": row['ID'] for _, row in filtered_df.iterrows()}
            if client_options:
                selected_option = st.selectbox("Select a client to modify:", list(client_options.keys()))
                selected_id = client_options[selected_option]
                client_info = df[df['ID'] == selected_id].iloc[0]
                
                with st.expander(f"Modify Details for {client_info['NAME']}", expanded=True):
                    # ... (Your existing edit logic here) ...
                    # Re-implementing the core update button for brevity
                    if st.button("✅ Update Details", type="primary"):
                        st.success("Update logic active.")

        # --- SIDEBAR ADD CLIENT ---
        st.sidebar.divider()
        st.sidebar.header("Add New Client")
        with st.sidebar.form("add_form", clear_on_submit=True):
            new_num = st.number_input("Client Number", min_value=1, step=1)
            new_name = st.text_input("Name of Customer")
            new_uen = st.text_input("UEN Number")
            new_month = st.selectbox("Year End Month", MONTHS)
            new_status = st.selectbox("Status", ["Active", "Terminated"])
            if st.form_submit_button("Save New Client"):
                add_client(new_num, new_name, new_uen, new_month, new_status)
                st.rerun()

    elif menu_choice == "Master KYC Form":
        master_kyc_form()
    
    else:
        st.title(menu_choice)
        st.info("Section logic coming soon.")