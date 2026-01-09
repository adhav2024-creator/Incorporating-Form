import streamlit as st
import pandas as pd
from database import init_db, get_clients, add_client, delete_client, update_client

# --- 1. CONFIGURATION & LOGIN ---
st.set_page_config(page_title="Audit & Incorporation Portal", layout="wide")
init_db()

MONTHS = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# State management to handle "Page Switching" without the sidebar
if "view" not in st.session_state:
    st.session_state["view"] = "management"
if "selected_client_for_kyc" not in st.session_state:
    st.session_state["selected_client_for_kyc"] = None

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

# --- 2. THE FORM BUILDING SECTION (Master KYC) ---
def master_kyc_form(client_name):
    st.button("⬅️ Back to Client Database", on_click=lambda: st.session_state.update({"view": "management"}))
    st.title(f"🛡️ Master KYC: {client_name}")
    
    with st.form("master_kyc_main"):
        st.subheader("Section 1: Entity Background")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("First Choice Company Name", value=client_name)
            st.text_area("Principal Business Activities")
        with col2:
            st.selectbox("Primary SSIC Code", ["62011", "70201", "46900", "Other"])
            st.text_input("Proposed Registered Office Address")

        st.divider()
        st.subheader("Section 2: Individual Stakeholders")
        num_ppl = st.number_input("Number of Stakeholders", 1, 10, 1)
        for i in range(int(num_ppl)):
            with st.expander(f"Stakeholder {i+1}", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Full Legal Name", key=f"n_{i}")
                    st.text_input("Identification Number", key=f"id_{i}")
                with c2:
                    st.text_input("Nationality", key=f"nat_{i}")
                    st.text_area("Residential Address", key=f"addr_{i}")
        
        if st.form_submit_button("Save and Finalize KYC"):
            st.success(f"KYC for {client_name} has been archived.")

# --- 3. MAIN LOGIC ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("Client Management System")
        df = get_clients()

        if not df.empty:
            # Formatting
            df['client_num'] = pd.to_numeric(df['client_num'], errors='coerce')
            df.columns = [col.replace('_', ' ').upper() for col in df.columns]

            # 📊 Practice Overview
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Total Clients", len(df))
            m_col2.metric("Active Portfolios", len(df[df['STATUS'] == 'Active']))
            
            st.divider()

            # 📋 Search and Database
            search_query = st.text_input("🔍 Search Client to Manage or Build Form", "")
            filtered_df = df.copy()
            if search_query:
                filtered_df = filtered_df[filtered_df['NAME'].str.contains(search_query, case=False, na=False)]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # --- THE ACTION BUTTONS ---
            st.subheader("🚀 Actions")
            client_to_kyc = st.selectbox("Select Client to Build KYC Form:", filtered_df['NAME'].tolist())
            
            col_a, col_b = st.columns([1, 4])
            if col_a.button("📝 Open KYC Form", type="primary"):
                st.session_state["selected_client_for_kyc"] = client_to_kyc
                st.session_state["view"] = "kyc_form"
                st.rerun()

    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_for_kyc"])