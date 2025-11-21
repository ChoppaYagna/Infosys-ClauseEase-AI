import streamlit as st

def init_session_state():
    """Initializes all default values in Streamlit's session state."""
    defaults = {
        "logged_in": False, "user_email": None, "user_name": None, "jwt_token": None, "account_id": None,
        "page": "login", "current_text": None,
        "simplified_text": None, 
        "simplification_level": "Intermediate", 
        "show_analysis": False, "reset_token": None, "chat_history": [],
        "rag_chain": None, "pending_prompt": None, "model_ready": False,
        "current_document_id": None, "current_file_name": None, "current_title": None,
        "active_workspace_tab": "Dashboard", "simplification_model": "FLAN-T5",
        "is_likely_legal": None, "uploaded_file_bytes": None,
        "uploaded_file_name": None, "uploaded_file_type": None,
        "uploaded_pdf_base64": None, "last_processed_view": None,
        "current_auth_image_index": 0,
        "theme": "light",
        "doc_analytics": None,
        "admin_selection": "Hide Admin",
        "is_admin": False,
        "ai_issues": [],
        "ai_risks": []
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v