# db/utils.py
import os

def tenant_db_path(account_id: int) -> str:
    init_db_path = "database"  # ideally parameterize this, maybe pass from settings
    return os.path.join(init_db_path, f"tenant_{account_id}.db")
