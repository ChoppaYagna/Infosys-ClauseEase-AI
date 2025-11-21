import streamlit as st
from db import tenant_db_path, get_tenant_user_id
from session_state import init_session_state
from processing import process_document_logic

def show_dashboard():
    """Displays the main application UI after a user is logged in."""
    
    # --- LAZY-LOAD HEAVY DEPENDENCIES ---
    # These are only loaded *after* the user logs in
    from views import dashboard_view
    from views import upload_view
    from views import assistant_view
    from views import chat_view
    from views import glossary_view
    from views import admin_view
    
    tenant_db = tenant_db_path(st.session_state.user_email)
    tenant_user_id = get_tenant_user_id(tenant_db, st.session_state.user_email)
    requested_tab = st.session_state.get("active_workspace_tab", "Dashboard")

    workspace_options = ["Dashboard", "Upload & Process", "Legal Assistant", "Chat Support", "Glossary"]
    try: default_workspace_index = workspace_options.index(requested_tab)
    except ValueError: default_workspace_index = 0

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("---"); st.markdown("**Workspace**")
        admin_selection = st.session_state.get("admin_selection", "Hide Admin")

        workspace_selection = st.radio(
            "workspace_nav", options=workspace_options, index=default_workspace_index, label_visibility="collapsed"
        )
        if workspace_selection != st.session_state.active_workspace_tab:
            st.session_state.active_workspace_tab = workspace_selection
            st.rerun()

        st.markdown("---"); st.markdown("**Simplification Model**")
        model_options = ["DistilBART", "BART-Large", "FLAN-T5"]
        model_selection = st.selectbox(
            "Select Model", options=model_options, index=model_options.index(st.session_state.get("simplification_model", "DistilBART")), label_visibility="collapsed"
        )
        if model_selection != st.session_state.simplification_model:
            st.session_state.simplification_model = model_selection
        st.caption(f"Using: {st.session_state.simplification_model}")
        st.markdown("---")

        if st.session_state.get("is_admin", False):
            with st.expander("Admin Panel"):
                
                admin_options = ["Hide Admin", "User Management", "Reports", "Tenant DB Inspector"]
                
                admin_selection_radio = st.radio(
                    "admin_nav", options=admin_options,
                    index=admin_options.index(admin_selection) if admin_selection in admin_options else 0,
                    key="admin_radio_expander", label_visibility="collapsed"
                )
                if admin_selection_radio != admin_selection:
                    st.session_state.admin_selection = admin_selection_radio
                    admin_selection = admin_selection_radio
                    st.rerun()

        with st.sidebar.expander("Account Info"):
            user_email = st.session_state.get('user_email', 'N/A')
            st.info(f"**Email:** {user_email}")
            st.success("**Status:** Active")
            
            st.markdown("---")
            if st.button("Logout", width='stretch', type="secondary", help="Click to log out"):
                keys_to_clear = ["logged_in", "user_email", "jwt_token", "account_id",
                                 "current_text", "simplified_text", "simplification_level",
                                 "doc_analytics", "rag_chain", "model_ready", "current_document_id",
                                 "chat_history", "current_file_name", "current_title",
                                 "admin_selection", "user_name", "is_admin", "ai_issues", "ai_risks"]
                if "oauth_state" in st.session_state:
                    keys_to_clear.append("oauth_state")
                    
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                init_session_state()
                st.rerun()

        with st.sidebar.expander("Theme Settings"):
            current_theme = st.session_state.get("theme", "light")
            theme_selection = st.radio(
                "Select Theme", options=["light", "dark"],
                index=0 if current_theme == "light" else 1, key="theme_radio", horizontal=True
            )
            if theme_selection != current_theme:
                st.session_state.theme = theme_selection
                st.rerun()

    # --- PAGE CONTENT ROUTER ---
    
    admin_selection_display = st.session_state.get("admin_selection", "Hide Admin")
    
    # --- If Admin Panel is selected, show it ---
    if admin_selection_display != "Hide Admin":
        admin_view.show_page(admin_selection_display)
    
    # --- Otherwise, show the selected user workspace ---
    elif workspace_selection == "Dashboard":
        dashboard_view.show_page(tenant_db, tenant_user_id)
    
    elif workspace_selection == "Upload & Process":
        upload_view.show_page(tenant_db, tenant_user_id, process_document_logic)
    
    elif workspace_selection == "Legal Assistant":
        assistant_view.show_page(tenant_db, tenant_user_id)
    
    elif workspace_selection == "Chat Support":
        chat_view.show_page(tenant_db, tenant_user_id)
    
    elif workspace_selection == "Glossary":
        glossary_view.show_page(tenant_db, tenant_user_id)