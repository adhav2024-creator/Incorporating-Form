import streamlit as st
import pandas as pd
from datetime import date

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Client Management & Incorporation", layout="wide")

# --- 2. CLONED SECURITY LOGIC ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "Awesome2050@":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Corporate Portal Login")
        st.text_input("Enter Professional Access Code", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Professional Access Code", type="password", on_change=password_entered, key="password")
        st.error("Invalid credentials.")
        return False
    return True

# --- 3. CLIENT MANAGEMENT MODULE (The "Cloned" Part) ---
def client_management_dashboard():
    st.header("👥 Client Management System")
    
    # Search and Filter logic as per your previous project
    search_query = st.text_input("Search Client Database (Name or Registration Number)")
    
    # Mock Data for illustration - this would usually pull from Azure PostgreSQL
    data = {
        "Company Name": ["ABC TECH PTE LTD", "GLOBAL TRADE CORP"],
        "Registration Number": ["202301010K", "202299887W"],
        "Status": ["Active", "Pending KYC"]
    }
    df = pd.DataFrame(data)
    
    if search_query:
        df = df[df['Company Name'].str.contains(search_query.upper())]
    
    st.table(df)
    
    if st.button("Add New Client to Registry"):
        st.info("Direct entry into management registry.")

# --- 4. INCORPORATION MODULE (The New "Master KYC") ---
def master_kyc_section():
    st.header("🛡️ Master KYC Form")
    st.subheader("New Incorporation Intake")
    
    with st.form("master_kyc_form"):
        # Section A: Entity Details
        st.write("### Section A: Proposed Entity")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Proposed Company Name (Primary)")
            st.text_area("Principal Business Activities")
        with c2:
            st.selectbox("Primary SSIC Code", ["62011", "70201", "46900", "Other"])
            st.text_input("Proposed Registered Office Address")
            
        st.divider()
        
        # Section B: Stakeholders
        st.write("### Section B: Individual Stakeholders")
        num_ppl = st.number_input("Number of Stakeholders", 1, 10, 1)
        for i in range(int(num_ppl)):
            with st.expander(f"Stakeholder {i+1} Details", expanded=True):
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.text_input("Full Legal Name", key=f"n_{i}")
                    st.text_input("Identification Number (NRIC/Passport)", key=f"id_{i}")
                with sc2:
                    st.text_input("Nationality", key=f"nat_{i}")
                    st.text_area("Residential Address", key=f"addr_{i}")
        
        if st.form_submit_button("Submit KYC for Approval"):
            st.success("Form submitted to management database.")

# --- 5. MAIN NAVIGATION HUB ---
def main():
    if check_password():
        st.sidebar.title("Main Menu")
        # Integrating the Client Management and the Incorporation Forms in one sidebar
        app_mode = st.sidebar.selectbox("Choose Module", [
            "Client Management Dashboard", 
            "1. Master KYC Form", 
            "2. BG Sec File", 
            "3. Customer Acceptance"
        ])

        if app_mode == "Client Management Dashboard":
            client_management_dashboard()
        elif app_mode == "1. Master KYC Form":
            master_kyc_section()
        else:
            st.title(app_mode)
            st.info("This section is ready for the long list of data points.")

if __name__ == "__main__":
    main()