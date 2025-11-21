from db.master_auth import verify_jwt_token
from db.tenant_db import save_document, save_chat_history
import os

def authenticate_request(auth_header: str):
    if not auth_header:
        return None, "Missing auth header"
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return None, "Invalid auth header format"
    payload = verify_jwt_token(token)
    if not payload:
        return None, "Invalid or expired token"
    return payload, None

def get_tenant_db_path(account_id: int) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    tenant_dir = os.path.join(base_dir, "database")  # adjust to your tenant db folder
    return os.path.join(tenant_dir, f"tenant_{account_id}.db")

def create_document(auth_header: str, file_name: str, title: str, text: str):
    payload, error = authenticate_request(auth_header)
    if error:
        return False, error
    account_id = payload['account_id']

    tenant_db = get_tenant_db_path(account_id)
    doc_id = save_document(tenant_db, account_id, file_name, title, text)
    return True, f"Document saved with id {doc_id}."

def save_chat(auth_header: str, document_id: int, history: list):
    payload, error = authenticate_request(auth_header)
    if error:
        return False, error
    account_id = payload['account_id']
    tenant_db = get_tenant_db_path(account_id)
    save_chat_history(tenant_db, document_id, account_id, history)
    return True, "Chat history saved."
