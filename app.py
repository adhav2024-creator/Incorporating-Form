import streamlit as st
import pandas as pd
from datetime import date

# --- 1. SETTINGS ---
# This MUST be the first Streamlit command
st.set_page_config(page_title="BG Consultancy | Incorporation Portal", layout="wide")

# --- 2. SECURITY CHECK ---
def check_password():
    """Returns True if the user has the correct password."""

    def password_entered():
        if st.session_state["password"] == "Awesome2050@":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # remove password from session state
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input
        st.title("🔒 Access Restricted")
        st.text_input("Please enter Access Code", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password was wrong
        st.title("🔒 Access Restricted")
        st.text_input("Please enter Access Code", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password is correct
        return True

# --- 3. MASTER KYC FORM LOGIC ---
def master_kyc_section():
    st.title("🛡️ Master KYC Form")
    st.info("Section 1: Detailed Entity and Stakeholder Information for AML/CFT Compliance.")

    with st.form("master_kyc_main_form"):
        # Section A: Entity Background
        st.subheader("Section A: Proposed Entity Information")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("First Choice Company Name")
            st.text_input("Second Choice Company Name")
            st.text_area("Detailed Description of Principal Business Activities")
        with col2:
            st.selectbox("Primary SSIC Code", ["62011", "70201", "46900", "64202", "Other"])
            st.text_input("Proposed Registered Office Address")
            st.selectbox("Office Type", ["Commercial Office", "Residential (Home Office Scheme)", "Service Provider Address"])

        st.divider()

        # Section B: Financial & Risk Profile
        st.subheader("Section B: Financial & Risk Profile")
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            st.selectbox("Primary Source of Wealth", ["Accumulated Salary", "Business Profits", "Investment Returns", "Inheritance", "Divestment of Assets"])
            st.text_input("Expected Annual Turnover (Singapore Dollars)")
            st.text_area("Countries of Incoming and Outgoing Funds")
        with fcol2:
            st.selectbox("Expected Number of Employees", ["1-5", "6-20", "21-50", "More than 50"])
            st.selectbox("Frequency of Transactions per Month", ["Low (1-10)", "Medium (11-50)", "High (More than 50)"])
            st.text_area("Reason for incorporating in Singapore (if foreign beneficial owners)")

        st.divider()

        # Section C: Individual Stakeholders
        st.subheader("Section C: Individual Stakeholders")
        st.write("Provide full details for all Directors, Shareholders, and Ultimate Beneficial Owners.")
        
        count = st.number_input("Number of Individuals to provide details for", 1, 10, 1)
        
        for i in range(int(count)):
            with st.expander(f"Individual {i+1} Details", expanded=True):
                r1c1, r1c2, r1c3 = st.columns([2, 1, 1])
                with r1c1:
                    st.text_input(f"Full Legal Name (as per ID)", key=f"n_{i}")
                with r1c2:
                    st.selectbox("Identification Type", ["NRIC", "Passport", "FIN"], key=f"it_{i}")
                with r1c3:
                    st.text_input("Identification Number", key=f"in_{i}")
                
                r2c1, r2c2, r2c3 = st.columns([2, 1, 1])
                with r2c1:
                    st.text_input("Residential Address", key=f"ra_{i}")
                with r2c2:
                    st.text_input("Nationality", key=f"nat_{i}")
                with r2c3:
                    st.text_input("Occupation", key=f"occ_{i}")
                
                st.write("Relationship/Role in Company:")
                role_cols = st.columns(3)
                role_cols[0].checkbox("Director", key=f"dir_{i}")
                role_cols[1].checkbox("Shareholder", key=f"sh_{i}")
                role_cols[2].checkbox("Politically Exposed Person (PEP)", key=f"pep_{i}")

        st.divider()

        st.subheader("Section D: Declaration")
        st.checkbox("I hereby declare that all information provided is true and accurate to the best of my knowledge.")
        
        if st.form_submit_button("Save Master KYC to Database"):
            st.success("Data captured successfully. Awaiting Azure Database Integration.")

# --- 4. MAIN NAVIGATION ---
def main():
    if check_password():
        # This sidebar only appears IF check_password returns True
        st.sidebar.title("Incorporation Modules")
        
        selection = st.sidebar.radio("Navigate to:", [
            "Dashboard", 
            "1. Master KYC Form", 
            "2. BG Sec File", 
            "3. Customer Acceptance Form"
        ])

        if selection == "Dashboard":
            st.title("Welcome to the Incorporation Portal")
            st.write("Select a module from the sidebar to begin.")
            
        elif selection == "1. Master KYC Form":
            master_kyc_section()
            
        elif selection == "2. BG Sec File":
            st.title("BG Sec File")
            st.warning("This section is under development.")

        elif selection == "3. Customer Acceptance Form":
            st.title("Customer Acceptance Form")
            st.warning("This section is under development.")

# Run the app
if __name__ == "__main__":
    main()