# auth.py (REVISED)

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import os

# --- Configuration ---

CLIENT_SECRETS_FILE = 'client_secrets.json'
REDIRECT_URI = 'http://localhost:8501'
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

# --- NEW: Hardcoded State ---
# This is a fixed string to prevent the session state from being lost.
# This MUST be a secret, random string.
HARDCODED_STATE = "a1b2c3d4e5f6_THIS_IS_MY_RANDOM_STATE_STRING_98765"

# --- OAuth Functions ---

def get_google_flow():
    """
    Creates a Google OAuth Flow object.
    It reads the client_secrets.json file AND sets a fixed state.
    """
    if not os.path.exists(CLIENT_SECRETS_FILE):
        st.error(f"Missing credentials file: {CLIENT_SECRETS_FILE}. Please download it from Google Cloud Console.")
        st.stop()
        
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=HARDCODED_STATE  # <-- ADDED: Pass the hardcoded state here
    )

def get_google_auth_url(flow):
    """
    Generates the authorization URL for the user to click.
    """
    authorization_url, _ = flow.authorization_url( # We no longer need the state
        access_type='offline',
        include_granted_scopes='true',
        #prompt='consent'
    )
    # st.session_state.oauth_state = state # <-- REMOVED: No longer need session state
    return authorization_url

def get_google_user_info(flow, auth_code):
    """
    Exchanges the authorization code for user credentials and info.
    The flow object will now automatically verify the state.
    """
    try:
        # Exchange the authorization code for an access token
        # This will now automatically check the 'state' from the URL
        # against the HARDCODED_STATE we set in the flow.
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        # Verify the ID token (which contains user info)
        request_session = requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request_session, credentials.client_id
        )
        
        # Return the user's information
        return {
            "name": id_info.get("name"),
            "email": id_info.get("email"),
            "picture": id_info.get("picture"),
        }
    except Exception as e:
        # If the state *still* doesn't match, an error will be raised here.
        st.error(f"Failed to fetch token or user info: {e}")
        return None