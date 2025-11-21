import streamlit as st
import os
import time
import base64
import auth # For Google OAuth
from streamlit_autorefresh import st_autorefresh
from utils import is_google_configured

# --- Import only the DB functions needed for auth ---
from db import (
    register_account,
    login_account,
    request_password_reset_token,
    reset_password_with_token,
    is_strong_password,
    create_tenant_db,
    tenant_db_path
)

# --- Image List for Toggling ---
AUTH_IMAGES = [
    "images/Gemini_Generated_Image_nedmxenedmxenedm.png", # Image 1
    "images/Gemini_Generated_Image_dnaml5dnaml5dnam.png", # Image 2
    "images/Gemini_Generated_Image_x3uudcx3uudcx3uu.png",     # Image 3
]
auth_images_exist = os.path.exists("images") and AUTH_IMAGES and os.path.exists(AUTH_IMAGES[0]) if AUTH_IMAGES else False


def show_auth_forms():
    """Displays the main Login/Sign Up form UI."""
    if "login_error" in st.session_state:
        st.error(st.session_state.login_error)
        del st.session_state.login_error
    
    if st.session_state.get("google_login_clicked"):
        with st.spinner("Redirecting to Google..."):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={st.session_state.google_auth_url}">', unsafe_allow_html=True)
            time.sleep(2)
        del st.session_state.google_login_clicked
        del st.session_state.google_auth_url
        st.stop()
        
    refresh_interval_ms = 8000
    if auth_images_exist:
        count = st_autorefresh(interval=refresh_interval_ms, key="auth_image_refresh")
        if count is not None:
            st.session_state.current_auth_image_index = (st.session_state.current_auth_image_index + 1) % len(AUTH_IMAGES)

    col_left, col_right = st.columns([1.1, 1], gap="large")
    with col_left:
        if not auth_images_exist:
            st.markdown("<div style='display: flex; align-items: center; justify-content: center; height: 100%; border: 1px dashed grey; border-radius: 8px; background-color: #FAFAFA;'><p style='color: grey;'>Image Area</p></div>", unsafe_allow_html=True)
            st.warning("Auth images not found.")
        else:
            current_image_path = AUTH_IMAGES[st.session_state.current_auth_image_index]
            
            # --- FIX: Replaced broken st.image/st.markdown combo with Base64 embedding ---
            try:
                # 1. Read the image file and encode it in Base64
                with open(current_image_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                
                # 2. Get the correct image format for the data URI
                img_ext = os.path.splitext(current_image_path)[1].lower().replace(".", "")
                if img_ext == 'jpg': img_ext = 'jpeg'
                
                # 3. Build the *entire* HTML block in one string
                html_content = f"""
                <div class='image-container'>
                    <img src="data:image/{img_ext};base64,{img_data}" style="max-width: 100%; height: auto; padding: 0 1.5rem;">
                    <h2 style='color: var(--primary-color-dark); text-align: center; margin-top: 1rem;'>Simplify Your Contracts</h2>
                    <p style='color: var(--text-color); text-align: center;'>Leverage AI to understand complex legal documents quickly and easily.</p>
                </div>
                """
                
                # 4. Render it all in *one* st.markdown call
                st.markdown(html_content, unsafe_allow_html=True)
                
            except Exception as e: 
                st.error(f"Error loading image '{current_image_path}': {e}")
            # --- *** END OF FIX *** ---

    with col_right:
        st.markdown("<h1 style='text-align: center; color: var(--primary-color-dark); margin-bottom: 20px;'>ClauseEase AI</h1>", unsafe_allow_html=True)
        tab_signin, tab_signup = st.tabs(["Sign In", "Sign Up"])
        with tab_signin:
            st.subheader("Log in to continue")
            st.markdown('<div class="form-label">Email Address</div>', unsafe_allow_html=True)
            email = st.text_input("signin_email", label_visibility="collapsed", placeholder="Enter your email")
            st.markdown('<div class="form-label">Password</div>', unsafe_allow_html=True)
            password = st.text_input("signin_password", type="password", label_visibility="collapsed", placeholder="Enter your password")
            if st.button("Sign In", width='stretch', type="primary", key="signin_btn"):
                if email and password:
                    ok, msg, token, account_id, is_admin = login_account(email, password)
                    if ok:
                        st.session_state.logged_in = True; st.session_state.user_email = email; st.session_state.jwt_token = token; st.session_state.account_id = account_id
                        st.session_state.user_name = email 
                        st.session_state.is_admin = is_admin 
                        tenant_db = tenant_db_path(email)
                        if not os.path.exists(tenant_db): create_tenant_db(email, account_id)
                        st.rerun()
                    else: st.error(msg)
                else: st.error("Enter email and password")
            if st.button("Forgot Password?", width='stretch', type="secondary", key="forgot_btn"):
                st.session_state.page = "forgot"; st.rerun()
            
            st.markdown('<div class="or-divider"><span>Other log in options</span></div>', unsafe_allow_html=True)
            if is_google_configured():
                try:
                    flow = auth.get_google_flow()
                    google_auth_url = auth.get_google_auth_url(flow)
                    GOOGLE_ICON_SVG = """<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M17.64 9.20455C17.64 8.56682 17.5827 7.95273 17.4764 7.36364H9V10.8409H13.8436C13.635 11.99 13.0009 12.96 12.0477 13.6114V15.8182H14.9564C16.6582 14.2818 17.64 11.9455 17.64 9.20455Z" fill="#4285F4"/><path fill-rule="evenodd" clip-rule="evenodd" d="M9 18C11.43 18 13.4673 17.1955 14.9564 15.8182L12.0477 13.6114C11.2318 14.1205 10.2182 14.4545 9 14.4545C6.96273 14.4545 5.22 13.0409 4.5 11.25H1.5V13.5114C3.00273 16.2 5.79545 18 9 18Z" fill="#34A853"/><path fill-rule="evenodd" clip-rule="evenodd" d="M4.5 11.25C4.29273 10.6364 4.18636 9.98409 4.18636 9.31591C4.18636 8.64773 4.29273 7.99545 4.5 7.38182V5.11136H1.5C0.542727 6.64773 0 8.21818 0 9.31591C0 10.4136 0.542727 11.9841 1.5 13.5205L4.5 11.25Z" fill="#FBBC05"/><path fill-rule="evenodd" clip-rule="evenodd" d="M9 3.54545C10.3214 3.54545 11.5077 4.01364 12.4405 4.91364L15.0218 2.33182C13.4673 0.886364 11.43 0 9 0C5.79545 0 3.00273 1.8 1.5 4.5L4.5 7.38182C5.22 5.59091 6.96273 3.54545 9 3.54545Z" fill="#EA4335"/></svg>"""
                    st.markdown(
                        f'<a href="{google_auth_url}" target="_self" class="google-auth-button">{GOOGLE_ICON_SVG} <span>Continue with Google</span></a>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Google login unavailable: {e}")
                    st.button("Continue with Google", width='stretch', type="secondary", disabled=True)
            else:
                st.button("Continue with Google", width='stretch', type="secondary", disabled=True)
                st.caption("Google login is not configured (`client_secrets.json` missing)")
                
        with tab_signup:
            st.subheader("Create your account")
            st.markdown('<div class="form-label">Full Name</div>', unsafe_allow_html=True)
            full_name = st.text_input("signup_name", label_visibility="collapsed", placeholder="Enter your full name")
            st.markdown('<div class="form-label">Email Address</div>', unsafe_allow_html=True)
            email_signup = st.text_input("signup_email", label_visibility="collapsed", placeholder="Enter your email ")
            st.markdown('<div class="form-label">Password</div>', unsafe_allow_html=True)
            password_signup = st.text_input("signup_password", type="password", label_visibility="collapsed", placeholder="Create a password")
            st.markdown('<div class="form-label">Confirm Password</div>', unsafe_allow_html=True)
            confirm_password = st.text_input("signup_confirm_password", type="password", label_visibility="collapsed", placeholder="Confirm your password")
            st.markdown('<div classa="password-req small-muted">Min 8 characters required</div>', unsafe_allow_html=True)
            
            if st.button("Sign Up", width='stretch', type="primary", key="signup_btn"):
                if all([full_name, email_signup, password_signup, confirm_password]):
                    if password_signup != confirm_password: st.error("Passwords do not match.")
                    elif not is_strong_password(password_signup):
                        st.error("Password must be >= 8 chars with uppercase, lowercase, digit, and symbol.")
                    else:
                        ok, msg, token, account_id, cleaned_email = register_account(email_signup, password_signup)
                        if ok:
                            time.sleep(0.1)
                            ok_login, msg_login, token, account_id, is_admin = login_account(cleaned_email, password_signup)
                            if ok_login:
                                st.session_state.logged_in = True
                                st.session_state.user_email = cleaned_email
                                st.session_state.jwt_token = token
                                st.session_state.account_id = account_id
                                st.session_state.user_name = full_name 
                                st.session_state.is_admin = is_admin 
                                tenant_db = tenant_db_path(st.session_state.user_email)
                                if not os.path.exists(tenant_db): create_tenant_db(st.session_state.user_email, account_id)
                                st.success("Account created!"); time.sleep(1); st.rerun()
                            else:
                                st.error(f"Account created, but auto-login failed: {msg_login}")
                                time.sleep(2); st.rerun()
                        else: st.error(msg)
                else: st.error("Please fill all fields")
            
            st.markdown('<div class="or-divider"><span>Or sign up with</span></div>', unsafe_allow_html=True)
            if is_google_configured():
                try:
                    flow = auth.get_google_flow()
                    google_auth_url = auth.get_google_auth_url(flow)
                    GOOGLE_ICON_SVG = """<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M17.64 9.20455C17.64 8.56682 17.5827 7.95273 17.4764 7.36364H9V10.8409H13.8436C13.635 11.99 13.0009 12.96 12.0477 13.6114V15.8182H14.9564C16.6582 14.2818 17.64 11.9455 17.64 9.20455Z" fill="#4285F4"/><path fill-rule="evenodd" clip-rule="evenodd" d="M9 18C11.43 18 13.4673 17.1955 14.9564 15.8182L12.0477 13.6114C11.2318 14.1205 10.2182 14.4545 9 14.4545C6.96273 14.4545 5.22 13.0409 4.5 11.25H1.5V13.5114C3.00273 16.2 5.79545 18 9 18Z" fill="#34A853"/><path fill-rule="evenodd" clip-rule="evenodd" d="M4.5 11.25C4.29273 10.6364 4.18636 9.98409 4.18636 9.31591C4.18636 8.64773 4.29273 7.99545 4.5 7.38182V5.11136H1.5C0.542727 6.64773 0 8.21818 0 9.31591C0 10.4136 0.542727 11.9841 1.5 13.5205L4.5 11.25Z" fill="#FBBC05"/><path fill-rule="evenodd" clip-rule="evenodd" d="M9 3.54545C10.3214 3.54545 11.5077 4.01364 12.4405 4.91364L15.0218 2.33182C13.4673 0.886364 11.43 0 9 0C5.79545 0 3.00273 1.8 1.5 4.5L4.5 7.38182C5.22 5.59091 6.96273 3.54545 9 3.54545Z" fill="#EA4335"/></svg>"""
                    st.markdown(
                        f'<a href="{google_auth_url}" target="_self" class="google-auth-button">{GOOGLE_ICON_SVG} <span>Continue with Google</span></a>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Google login unavailable: {e}")
                    st.button("Continue with Google", width='stretch', type="secondary", disabled=True)
            else:
                st.button("Continue with Google", width='stretch', type="secondary", disabled=True)
                st.caption("Google login is not configured (`client_secrets.json` missing)")

@st.dialog("Reset Password")
def show_forgot_password_form():
    """Displays the modal dialog for resetting a password."""
    st.markdown('<div class="form-label">Email Address</div>', unsafe_allow_html=True)
    email = st.text_input("Email", key="forgot_email_input", label_visibility="collapsed")
    
    if st.button("Get Reset Token", width='stretch', key="get_token_btn"):
        if email:
            ok, msg, token = request_password_reset_token(email) 
            if ok:
                st.success(msg) 
                if token: 
                    st.info(f"Email not configured. Demo token: {token}")
            else: 
                st.error(msg) 
        else: 
            st.warning("Please enter your email address.")

    token_input = st.text_input("Reset Token", key="reset_token_input", help="Enter the token received (or shown above for demo).")
    new_password = st.text_input("New Password", type="password", key="new_password_input", help="Enter your new password (min 8 chars).")
    confirm_new_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password_input")

    if st.button("Reset Password", width='stretch', type="primary", key="reset_pw_btn"):
        if not all([email, token_input, new_password, confirm_new_password]): st.error("Please fill all fields.")
        elif new_password != confirm_new_password: st.error("New passwords do not match.")
        elif not is_strong_password(new_password):
            st.error("New password must be >= 8 chars with uppercase, lowercase, digit, and symbol.")
        else:
            ok, msg = reset_password_with_token(email, token_input, new_password)
            if ok:
                st.success("Password reset successfully. You can now log in.")
                time.sleep(2); st.session_state.page = "login"; st.rerun()
            else: st.error(msg)

    if st.button("Back to Login", width='stretch', type="secondary", key="back_to_login_btn"):
        st.session_state.page = "login"; st.rerun()