# db/__init__.py
# FINAL CORRECT VERSION (Design 2)

# --- From tenant_db.py (The SINGLE source of truth for tenant logic) ---
from .tenant_db import (
    tenant_db_path,
    create_tenant_db,
    init_tenant_db,
    get_tenant_user_id,
    save_document,  # <-- This now correctly refers to the new 9-argument function
    save_chat_history,
    load_chat_history,
    get_glossary_terms,
    add_glossary_term,
    delete_glossary_term,
    get_user_and_doc_counts,
    get_all_users,
    get_all_documents,
    get_table,
    update_glossary_from_ai_output,
    extract_explanation_for_term
)

# --- From master_db.py (The SINGLE source of truth for master logic) ---
from .master_db import (
    init_master_db
)

# --- From master_auth.py (The SINGLE source of truth for auth logic) ---
from .master_auth import (
    register_account,
    login_account,
    request_password_reset_token,
    reset_password_with_token,
    verify_jwt_token,
    generate_jwt_token,
    is_strong_password,
    get_all_accounts_from_master,
    get_table_from_master,
    get_account_details_by_email
)