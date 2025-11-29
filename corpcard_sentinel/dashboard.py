import streamlit as st
import requests
import pandas as pd

# API Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="CorpCard Sentinel Admin", layout="wide")
st.title("🛡️ CorpCard Sentinel Admin Dashboard")

# Create Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Live Simulation", "Card Management", "Policy Control", "Audit Logs"])

# --- Tab 1: Live Simulation ---
with tab1:
    st.header("Simulate Transaction")
    
    with st.form("simulation_form"):
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.number_input("User ID", min_value=1, step=1)
            amount = st.number_input("Amount", min_value=0.0, step=0.01)
        with col2:
            merchant = st.text_input("Merchant Name")
            category = st.selectbox("Category", ["Electronics", "Travel", "Food", "Retail", "Other"])
            
        submitted = st.form_submit_button("Simulate Transaction")
        
        if submitted:
            payload = {
                "user_id": user_id,
                "amount": amount,
                "merchant": merchant,
                "category": category
            }
            
            try:
                response = requests.post(f"{API_BASE_URL}/simulate_transaction", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('is_violation'):
                        st.error(f"🚨 FRAUD DETECTED - CARD FROZEN 🚨\nReason: {result.get('violation_reason')}")
                        st.json(result)
                    else:
                        st.success(f"Transaction Allowed\nAnalysis: {result.get('violation_reason')}")
                        st.json(result)
                elif response.status_code == 403:
                    st.error("🚨 FRAUD DETECTED - CARD FROZEN 🚨")
                    st.json(response.json())
                else:
                    st.warning(f"Unexpected Status: {response.status_code}")
                    st.write(response.text)
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to API. Is it running?")

# --- Tab 2: Card Management ---
with tab2:
    st.header("User & Card Management")
    
    if st.button("Refresh Users"):
        st.rerun()
        
    try:
        response = requests.get(f"{API_BASE_URL}/users")
        if response.status_code == 200:
            users = response.json()
            if users:
                df = pd.DataFrame(users)
                
                # Highlight frozen cards
                def highlight_frozen(s):
                    return ['background-color: #ffcccc; color: black' if v == 'FROZEN' else '' for v in s]
                
                st.dataframe(df.style.apply(highlight_frozen, subset=['card_status']), use_container_width=True)
                
                # Unfreeze Action
                st.subheader("Unfreeze User")
                col_u1, col_u2 = st.columns([1, 3], vertical_alignment="bottom")
                with col_u1:
                    unfreeze_id = st.number_input("User ID to Unfreeze", min_value=1, step=1, key="unfreeze_id")
                with col_u2:
                    if st.button("Unfreeze Card"):
                        try:
                            uf_response = requests.post(f"{API_BASE_URL}/users/{unfreeze_id}/unfreeze")
                            if uf_response.status_code == 200:
                                st.success(f"User {unfreeze_id} card unfrozen successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to unfreeze: {uf_response.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.info("No users found.")
        else:
            st.error(f"Failed to fetch users: {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to API. Is it running?")

# --- Tab 3: Policy Control ---
with tab3:
    st.header("Policy Control")
    
    # List Policies
    st.subheader("Active Policies")
    try:
        response = requests.get(f"{API_BASE_URL}/policies")
        if response.status_code == 200:
            policies = response.json()
            if policies:
                for policy in policies:
                    with st.expander(f"{policy.get('rule_name', 'Policy')} (ID: {policy.get('id')})"):
                        st.write(f"**Description:** {policy.get('description')}")
                        
                        col_edit, col_delete = st.columns(2)
                        
                        # Edit Section
                        with col_edit:
                            with st.popover("Edit Policy"):
                                with st.form(f"edit_policy_{policy['id']}"):
                                    new_name = st.text_input("Name", value=policy.get('rule_name'))
                                    new_desc = st.text_area("Description", value=policy.get('description'))
                                    submitted = st.form_submit_button("Update")
                                    if submitted:
                                        update_payload = {
                                            "rule_name": new_name,
                                            "description": new_desc,
                                            "is_active": True
                                        }
                                        try:
                                            res = requests.put(f"{API_BASE_URL}/policies/{policy['id']}", json=update_payload)
                                            if res.status_code == 200:
                                                st.success("Updated!")
                                                st.rerun()
                                            else:
                                                st.error(f"Error: {res.text}")
                                        except Exception as e:
                                            st.error(f"Error: {e}")

                        # Delete Section
                        with col_delete:
                            if st.button("Delete Policy", key=f"del_{policy['id']}"):
                                try:
                                    res = requests.delete(f"{API_BASE_URL}/policies/{policy['id']}")
                                    if res.status_code == 200:
                                        st.success("Deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {res.text}")
                                except Exception as e:
                                    st.error(f"Error: {e}")
            else:
                st.info("No policies found.")
        else:
            st.error(f"Failed to fetch policies: {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to API. Is it running?")
        
    st.divider()
    
    # Create Policy
    st.subheader("Create New Policy")
    with st.form("create_policy_form"):
        p_name = st.text_input("Policy Name")
        p_desc = st.text_area("Description")
        # For simplicity, we aren't adding complex rule editing here as per requirements "Generic form"
        
        p_submitted = st.form_submit_button("Create Policy")
        
        if p_submitted:
            if p_name and p_desc:
                payload = {
                    "rule_name": p_name,
                    "description": p_desc
                    # Add other fields if required by the schema, assuming simple create for now
                }
                try:
                    cp_response = requests.post(f"{API_BASE_URL}/policies", json=payload)
                    if cp_response.status_code == 200:
                        st.success("Policy created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create policy: {cp_response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please fill in all fields.")

# --- Tab 4: Audit Logs ---
with tab4:
    st.header("Transaction Audit Logs")
    
    if st.button("Refresh Logs"):
        st.rerun()
        
    try:
        # Fetch Transactions
        t_response = requests.get(f"{API_BASE_URL}/transactions")
        # Fetch Users for name mapping
        u_response = requests.get(f"{API_BASE_URL}/users")
        
        if t_response.status_code == 200 and u_response.status_code == 200:
            transactions = t_response.json()
            users = u_response.json()
            
            if transactions:
                df = pd.DataFrame(transactions)
                
                # Map User ID to Name
                user_map = {u['id']: u['name'] for u in users}
                df['User Name'] = df['user_id'].map(user_map)
                
                # Rename and Select Columns
                df['Status'] = df['is_violation'].apply(lambda x: 'VIOLATION' if x else 'ALLOWED')
                df['Reason'] = df['violation_reason']
                df['Time'] = pd.to_datetime(df['timestamp'])
                
                display_df = df[['Time', 'User Name', 'merchant', 'amount', 'Status', 'Reason']].copy()
                display_df.columns = ['Time', 'User Name', 'Merchant', 'Amount', 'Status', 'Reason']
                
                # Styling
                def highlight_status(row):
                    bg_color = '#ffcccc' if row['Status'] == 'VIOLATION' else '#ccffcc'
                    text_color = 'black'
                    return [f'background-color: {bg_color}; color: {text_color}'] * len(row)
                
                st.dataframe(display_df.style.apply(highlight_status, axis=1), use_container_width=False, height=500)
            else:
                st.info("No transactions found.")
        else:
            st.error("Failed to fetch data.")
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to API. Is it running?")
