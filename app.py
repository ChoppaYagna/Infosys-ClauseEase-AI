# --------------------------
# LIGHTWEIGHT IMPORTS
# --------------------------
import streamlit as st
import os
import time
from dotenv import load_dotenv
import auth # For Google OAuth

# --- DB IMPORTS (Only what's needed for setup/routing) ---
try:
    from db import (
        init_master_db,
        verify_jwt_token,
        generate_jwt_token,
        get_account_details_by_email,
        register_account, # Needed for Google OAuth callback
        tenant_db_path,
        create_tenant_db
    )
except ImportError as e:
    st.error(f"Failed to import from 'db' package. Check your db/__init__.py file. Error: {e}")
    st.stop()
except Exception as e:
    st.error(f"A critical error occurred during DB import: {e}")
    st.stop()

# --- LOCAL MODULE IMPORTS ---
from session_state import init_session_state
from styling import inject_css
from auth_ui import show_auth_forms, show_forgot_password_form
from dashboard_ui import show_dashboard
from session_state import init_session_state

# --------------------------
# SETUP
# --------------------------
load_dotenv()

# --- Page Config (MUST be first and ONLY Streamlit command) ---
st.set_page_config(
    page_title="Contract Simplifier",
    page_icon="page",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Initialize ---
init_master_db()
init_session_state()
inject_css()


# --------------------------
# Main Router 
# --------------------------

query_params = st.query_params

if st.session_state.get("google_login_clicked"):
    st.empty() 
    with st.spinner("Redirecting to Google..."):
        st.markdown(f'<meta http-equiv="refresh" content="0; url={st.session_state.google_auth_url}">', unsafe_allow_html=True)
        time.sleep(5) 
    
    if "google_login_clicked" in st.session_state:
        del st.session_state.google_login_clicked
    if "google_auth_url" in st.session_state:
        del st.session_state.google_auth_url
    st.stop()

# --- Google OAuth Callback Handling (FIXED) ---
elif "code" in query_params:
    
    # --- FIX: Use st.columns to center content, do NOT call st.set_page_config ---
    col1, col_center, col3 = st.columns([1, 1.5, 1])
    
    with col_center:
        st.title("Logging In...")
        st.markdown("Please wait while we securely authenticate your Google account. This may take a moment.")

        with st.status("Authenticating...", expanded=True) as status:
            GOOGLE_OAUTH_DUMMY_PASSWORD = "GoogleUser_!@#_12345"
            login_success = False
            error_message = None

            try:
                status.write("Contacting Google to verify token...")
                flow = auth.get_google_flow()
                user_info = auth.get_google_user_info(flow, query_params.get("code"))
                
                if user_info:
                    google_email = user_info.get("email")
                    google_name = user_info.get("name", google_email) 
                    
                    status.write(f"Welcome, {google_name}! Setting up your account...")
                    
                    ok_reg, msg_reg, token_reg, acc_id_reg, cleaned_email_reg = register_account(google_email, GOOGLE_OAUTH_DUMMY_PASSWORD)
                    
                    if ok_reg:
                        st.session_state.logged_in = True
                        st.session_state.user_email = cleaned_email_reg
                        st.session_state.user_name = google_name 
                        st.session_state.jwt_token = token_reg
                        st.session_state.account_id = acc_id_reg
                        st.session_state.is_admin = False 
                        login_success = True
                    
                    elif msg_reg == "Email already registered.":
                        account_details = get_account_details_by_email(google_email)
                        if account_details:
                            st.session_state.logged_in = True
                            st.session_state.user_email = account_details["email"]
                            st.session_state.user_name = google_name 
                            st.session_state.jwt_token = generate_jwt_token(
                                account_details["email"],
                                account_details["id"],
                                bool(account_details["is_admin"])
                            )
                            st.session_state.account_id = account_details["id"]
                            st.session_state.is_admin = bool(account_details["is_admin"])
                            login_success = True
                        else:
                            error_message = f"Account for {google_email} exists but could not be retrieved."
                    else:
                        error_message = f"Failed to create Google user account: {msg_reg}"
                else:
                    error_message = "OAuth state mismatch or missing. Please try logging in again."
            
            except Exception as e:
                error_message = f"An error occurred during Google authentication: {e}"
            
            # --- Update status based on success ---
            if login_success:
                status.write("Account setup complete. Redirecting...")
                status.update(label="Login Successful!", state="complete", expanded=False)
                time.sleep(1) # Give user time to read
            else:
                status.update(label=f"Login Failed: {error_message}", state="error", expanded=True)
                time.sleep(3) # Give user time to read
            
    # --- This logic remains outside the 'with col_center' block ---
    st.query_params.clear()
    
    if login_success:
        # --- FIX: Removed invalid st.set_page_config call ---
        tenant_db = tenant_db_path(st.session_state.user_email)
        if not os.path.exists(tenant_db):
            create_tenant_db(st.session_state.user_email, st.session_state.account_id)
        time.sleep(0.5) 
        st.rerun()
    else:
        st.session_state.page = "login"
        st.session_state.login_error = error_message or "An unknown login error occurred."
        time.sleep(0.5)
        st.rerun()
# --- *** END OF UI UPDATE *** ---
            
# --- Forgot Password Page (FIXED) ---
elif st.session_state.page == "forgot":
    # --- FIX: Removed invalid st.set_page_config call. @st.dialog centers automatically. ---
    show_forgot_password_form()

# --- Main Logged-In View (FIXED) ---
elif st.session_state.get('logged_in', False):
    # --- FIX: Removed invalid st.set_page_config call. Layout is set once at top. ---
    if 'jwt_token' in st.session_state and verify_jwt_token(st.session_state.jwt_token):
        show_dashboard() # This will now lazy-load views and models
    else:
        st.error("Session invalid or expired. Please log in again.")
        keys_to_clear = ["logged_in", "user_email", "jwt_token", "account_id", 
                         "current_text", "simplified_text", "simplification_level",
                         "rag_chain", "model_ready", "current_document_id", "chat_history", 
                         "admin_selection", "user_name", "is_admin", "ai_issues", "ai_risks"]
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        init_session_state(); st.session_state.page = "login"; time.sleep(1); st.rerun()

# --- Default to Login Page (FIXED) ---
else:
    # --- FIX: Removed invalid st.set_page_config call. Layout is set once at top. ---
    show_auth_forms()