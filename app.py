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
    
    st.title(f"🛡️ Master KYC Form: {client_name}")
    with st.form("kyc_form"):
        st.subheader("Section 1: Entity Background")
        st.text_input("Proposed Company Name", value=client_name)
        st.text_area("Principal Business Activities")
        
        st.divider()
        st.subheader("Section 2: Individual Stakeholders")
        num = st.number_input("Number of Individuals", 1, 10, 1)
        
        # This is where the "long list" of fields will continue to grow
        if st.form_submit_button("Save Master KYC"):
            st.success(f"KYC Data for {client_name} Saved.")

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
            # Formatting headers to Uppercase
            df.columns = [col.replace('_', ' ').upper() for col in df.columns]
            
            # Add the "NEW FORM" column for interaction
            df["NEW FORM"] = False
            
            # Reorder: Put NEW FORM first, keep ID for background logic
            cols = ["NEW FORM"] + [c for c in df.columns if c != "NEW FORM"]
            df_display = df[cols]

            st.subheader("📋 Client Database")
            
            # INTERACTIVE TABLE
            edited_df = st.data_editor(
                df_display,
                hide_index=True,
                use_container_width=True,
                disabled=[c for c in df_display.columns if c != "NEW FORM"],
                key="main_table"
            )

            # Check if "NEW FORM" was checked
            clicked_rows = edited_df[edited_df["NEW FORM"] == True]
            if not clicked_rows.empty:
                st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()

            st.divider()

            # --- EDIT / DELETE SECTION (RESTORED & FULLY FUNCTIONAL) ---
            st.subheader("📝 Edit or Delete Client Details")
            
            # Search to help find client to edit
            search_edit = st.text_input("Search Client to Edit")
            edit_df = df.copy()
            if search_edit:
                edit_df = edit_df[edit_df['NAME'].str.contains(search_edit.upper(), na=False)]

            client_options = {f"{row['NAME']} (ID: {row['ID']})": row['ID'] for _, row in edit_df.iterrows()}
            
            if client_options:
                selected_option = st.selectbox("Select a client to modify:", list(client_options.keys()))
                selected_id = client_options[selected_option]
                
                # Fetch original data for the selected ID
                client_info = df[df['ID'] == selected_id].iloc[0]
                
                with st.expander(f"Modify Details for {client_info['NAME']}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_num = st.number_input("Client Number", value=int(client_info['CLIENT NUM']), key="ed_num")
                        edit_name = st.text_input("Customer Name", value=str(client_info['NAME']), key="ed_name")
                        edit_uen = st.text_input("UEN", value=str(client_info['UEN']), key="ed_uen")
                    with col2:
                        curr_month = str(client_info['YEAR END'])
                        m_idx = MONTHS.index(curr_month) if curr_month in MONTHS else 0
                        edit_month = st.selectbox("Year End", MONTHS, index=m_idx, key="ed_month")
                        
                        stat_list = ["Active", "Terminated"]
                        curr_stat = str(client_info['STATUS'])
                        s_idx = stat_list.index(curr_stat) if curr_stat in stat_list else 0
                        edit_status = st.selectbox("Client Status", stat_list, index=s_idx, key="ed_stat")

                    eb_col1, eb_col2, _ = st.columns([1, 1, 2])
                    if eb_col1.button("✅ Update Details", type="primary"):
                        update_client(int(selected_id), edit_num, edit_name, edit_uen, edit_month, edit_status)
                        st.success("Details Updated")
                        st.rerun()
                        
                    if eb_col2.button("🗑️ Delete Client"):
                        delete_client(int(selected_id))
                        st.warning("Client Deleted")
                        st.rerun()
            else:
                st.info("No clients found to edit.")
        else:
            st.info("Database is empty. Add a client from the sidebar.")

    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])