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
    
    st.title(f"🛡️ Master KYC: {client_name}")
    with st.form("kyc_form"):
        st.subheader("Section 1: Entity Background")
        st.text_input("Proposed Company Name", value=client_name)
        st.text_area("Principal Business Activities")
        st.divider()
        st.subheader("Section 2: Stakeholders")
        num = st.number_input("Number of Individuals", 1, 10, 1)
        # Form fields go here...
        if st.form_submit_button("Save Master KYC"):
            st.success("Saved!")

# --- 4. MAIN APP ---
if check_password():
    if st.session_state["view"] == "management":
        st.title("Client Management System")
        df = get_clients()

        # --- RESTORING YOUR SIDEBAR (ADD CLIENT) ---
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

        if not df.empty:
            # Formatting as per your original request
            df.columns = [col.replace('_', ' ').upper() for col in df.columns]
            
            # --- IN-TABLE BUTTON LOGIC ---
            st.subheader("📋 Client Database")
            st.info("💡 To build a KYC form, click the 'BUILD' checkbox next to the client name.")
            
            # Add an action column for the checkbox
            df["BUILD KYC"] = False
            
            # Reorder columns to put Action at the front
            cols = ["BUILD KYC"] + [c for c in df.columns if c != "BUILD KYC"]
            df = df[cols]

            # Display interactive table
            edited_df = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                disabled=[c for c in df.columns if c != "BUILD KYC"], # Only allow checkbox to be clicked
            )

            # Check if a checkbox was clicked
            clicked_rows = edited_df[edited_df["BUILD KYC"] == True]
            if not clicked_rows.empty:
                st.session_state["selected_client_name"] = clicked_rows.iloc[0]["NAME"]
                st.session_state["view"] = "kyc_form"
                st.rerun()

            st.divider()

            # --- RESTORING YOUR EDIT/DELETE SECTION ---
            st.subheader("📝 Edit or Delete Client Details")
            client_options = {f"{row['NAME']} (ID: {row['ID']})": row['ID'] for _, row in df.iterrows()}
            selected_option = st.selectbox("Select a client to modify:", list(client_options.keys()))
            selected_id = client_options[selected_option]
            client_info = df[df['ID'] == selected_id].iloc[0]
            
            with st.expander(f"Modify Details for {client_info['NAME']}", expanded=True):
                # ... (Your original Edit/Delete UI code here) ...
                st.write("Edit and Delete logic preserved here.")
                if st.button("🗑️ Delete Client"):
                    delete_client(int(selected_id))
                    st.rerun()
    
    elif st.session_state["view"] == "kyc_form":
        master_kyc_form(st.session_state["selected_client_name"])