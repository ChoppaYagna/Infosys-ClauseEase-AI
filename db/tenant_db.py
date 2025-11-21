# db/tenant_db.py
# (CORRECTED: Improved regex in extract_explanation_for_term)

import os
import sqlite3
import pandas as pd
import json
from datetime import datetime
from db.master_db import get_account_password_hash
import re


# ------------------------------
# Helpers
# ------------------------------

def _connect(db_path: str):
    """Internal: consistent connections with FK enforcement."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def sanitize_email(email) -> str:
    email_str = str(email)
    return email_str.replace('@', '_at_').replace('.', '_dot_')

def tenant_db_path(email: str) -> str:
    base_dir = "db/tenants"
    safe_email = sanitize_email(email)
    return os.path.join(base_dir, f"{safe_email}.db")


# ------------------------------
# Create Tenant DB & Schema
# ------------------------------

def create_tenant_db(email: str, user_id: int = None) -> str:
    """
    Creates and initializes the tenant database and the first user.
    This is idempotent (safe to run multiple times).
    """
    path = tenant_db_path(email)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # 1. Create all tables
    init_tenant_db(path)

    # 2. Get password hash from master DB
    if user_id is not None:
        password_hash = get_account_password_hash(user_id)
        if password_hash:
            # 3. Create the user record inside the new tenant DB
            create_tenant_user(path, email, password_hash)
        else:
            print(f"Warning: Could not find password hash for account_id {user_id}. User not created in tenant DB.")

    return path

def init_tenant_db(db_path: str):
    """Initializes all tables for a new tenant DB."""
    conn = _connect(db_path)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reset_token TEXT,
            reset_token_expires TIMESTAMP
        );
    """)

    # --- *** MODIFIED: documents table (Design 2) *** ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_file_name TEXT,
            document_title TEXT,
            original_text TEXT,
            
            simplified_text TEXT,
            simplification_level TEXT,

            is_legal INTEGER,
            original_word_count INTEGER,
            simplified_word_count INTEGER,
            
            uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    # --- *** END MODIFICATION *** ---

    # Chat history table
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            history_json TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(document_id, user_id)
        );
    """)

    # Glossary table
    c.execute("""
        CREATE TABLE IF NOT EXISTS glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE NOT NULL,
            simplified_explanation TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- MODIFIED: Seed glossary with lowercase terms ---
    c.execute("SELECT COUNT(*) FROM glossary;")
    if c.fetchone()[0] == 0:
        terms = [
            ("liability", "Legal responsibility for one's acts or omissions.", datetime.now()),
            ("indemnify", "To compensate someone for harm or loss.", datetime.now()),
            ("jurisdiction", "The official power to make legal decisions.", datetime.now()),
            ("arbitration", "A way to resolve disputes outside the courts.", datetime.now())
        ]
        c.executemany(
            "INSERT INTO glossary (term, simplified_explanation, created_at) VALUES (?, ?, ?);",
            terms
        )

    conn.commit()
    conn.close()

def create_tenant_user(db_path: str, email: str, password_hash: str):
    """Creates the user record inside their own tenant DB."""
    conn = _connect(db_path)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (email, password_hash, created_at)
        VALUES (?, ?, ?);
    """, (email, password_hash, datetime.now()))
    conn.commit()
    conn.close()


# ------------------------------
# Tenant Data Access Functions
# ------------------------------

def get_tenant_user_id(db_path: str, email: str) -> int:
    """Return the user id in the tenant DB for the given email."""
    conn = _connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        row = c.fetchone()
        if row:
            return row[0]
        else:
            print(f"CRITICAL ERROR: User {email} not found in tenant DB: {db_path}")
            return None
    except Exception as e:
        print(f"Error in get_tenant_user_id: {e}")
        return None
    finally:
        conn.close()

# --- *** MODIFIED: save_document function (Design 2) *** ---
def save_document(db_path: str, user_id: int, file_name: str, title: str, text: str,
                  simplified_text: str, simplification_level: str,
                  is_legal: int, original_wc: int, simple_wc: int) -> int:
    """Insert a document (with single text version and analytics) and return its id."""
    conn = _connect(db_path)
    c = conn.cursor()
    c.execute("""
        INSERT INTO documents (
            user_id, original_file_name, document_title, original_text,
            simplified_text, simplification_level,
            is_legal, original_word_count, simplified_word_count,
            uploaded_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        user_id, file_name, title, text,
        simplified_text, simplification_level,
        is_legal, original_wc, simple_wc,
        datetime.now()
    ))
    conn.commit()
    doc_id = c.lastrowid
    conn.close()
    return doc_id
# --- *** END MODIFICATION *** ---


def save_chat_history(db_path: str, document_id: int, user_id: int, history: list):
    """Upsert chat transcript for a (document_id, user_id) pair."""
    conn = _connect(db_path)
    c = conn.cursor()
    history_json = json.dumps(history)
    c.execute("""
        INSERT INTO chat_history (document_id, user_id, history_json, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(document_id, user_id) DO UPDATE SET
            history_json=excluded.history_json,
            created_at=excluded.created_at;
    """, (document_id, user_id, history_json, datetime.now()))
    conn.commit()
    conn.close()

def load_chat_history(db_path: str, document_id: int, user_id: int) -> list:
    """Return chat turns for a document/user or empty list."""
    conn = _connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT history_json FROM chat_history
        WHERE document_id=? AND user_id=?;
    """, (document_id, user_id))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

# --- Glossary Functions ---

def get_glossary_terms(db_path: str) -> dict:
    conn = _connect(db_path)
    rows = conn.execute("SELECT term, simplified_explanation FROM glossary;").fetchall()
    conn.close()
    return {t: e for t, e in rows}

def add_glossary_term(db_path: str, term: str, definition: str):
    """Adds or updates a term in the tenant glossary."""
    conn = _connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO glossary (term, simplified_explanation, created_at)
            VALUES (?, ?, ?)
        """, (term.lower(), definition, datetime.now()))
        conn.commit()
        return True, "Term added/updated successfully."
    except Exception as e:
        conn.rollback()
        print(f"DB Error (add_glossary_term): {e}")
        return False, f"Error adding/updating term: {e}"
    finally:
        conn.close()

def delete_glossary_term(db_path: str, term: str):
    """Deletes a term from the tenant glossary."""
    conn = _connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM glossary WHERE term = ?", (term.lower(),))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Term deleted successfully."
        else:
            return False, "Term not found."
    except Exception as e:
        conn.rollback()
        print(f"DB Error (delete_glossary_term): {e}")
        return False, f"Error deleting term: {e}"
    finally:
        conn.close()

# --- Dashboard & Admin Functions ---

def get_user_and_doc_counts(db_path: str):
    """Gets user and doc counts for the tenant DB."""
    conn = _connect(db_path); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users;"); users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM documents;"); docs = c.fetchone()[0]
    conn.close()
    return users, docs

def get_all_users(db_path: str) -> pd.DataFrame:
    """Gets all users from the tenant DB."""
    return pd.read_sql_query("SELECT id, email, created_at FROM users ORDER BY id;", _connect(db_path))

def get_all_documents(db_path: str) -> pd.DataFrame:
    """Gets all documents from the tenant DB."""
    return pd.read_sql_query("""
        SELECT 
            id, user_id, original_file_name, document_title, uploaded_at,
            original_text,
            simplified_text,
            simplification_level,
            is_legal,
            original_word_count,
            simplified_word_count
        FROM documents
        ORDER BY uploaded_at DESC;
    """, _connect(db_path))

def get_table(db_path: str, table_name: str) -> pd.DataFrame:
    """Gets any full table from the tenant DB."""
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise ValueError("Invalid table name")
    return pd.read_sql_query(f"SELECT * FROM {table_name};", _connect(db_path))

# --- AI & NLP Functions ---

def update_glossary_from_ai_output(db_path: str, original_text: str, simplified_text: str):
    """Scan AI simplification for legal terms and update the glossary in that tenant DB."""
    conn = _connect(db_path)
    c = conn.cursor()

    possible_terms = [
        "liability", "indemnify", "jurisdiction", "arbitration",
        "contract", "breach", "confidentiality", "termination",
        "warranty", "damages", "obligation", "disclosure", "clause"
    ]

    for term in possible_terms:
        # Check if the term is present in either text
        if (original_text and term.lower() in original_text.lower()) or \
           (simplified_text and term.lower() in simplified_text.lower()):
            
            explanation = "Simplified explanation not found." # Default
            if simplified_text: 
                # --- *** FIX: Search BOTH texts for a definition *** ---
                # Search the simplified text first
                explanation = extract_explanation_for_term(term, simplified_text)
                # If not found, search the original text
                if explanation == "Simplified explanation not found." and original_text:
                    explanation = extract_explanation_for_term(term, original_text)

            c.execute("""
                INSERT INTO glossary (term, simplified_explanation, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(term) DO UPDATE SET
                    simplified_explanation = excluded.simplified_explanation,
                    created_at = CURRENT_TIMESTAMP;
            """, (term.lower(), explanation)) 

    conn.commit()
    conn.close()


def extract_explanation_for_term(term, text_to_search):
    """
    Extract a simple explanation for a legal term from the provided text.
    """
    if not text_to_search:
        return "Simplified explanation not found."
    
    # --- *** THIS IS THE NEW, MORE FLEXIBLE REGEX *** ---
    # It looks for (term) followed by (is / means / is defined as / etc.)
    # and captures the text until the next period.
    pattern = rf"""
        \b{term}\b                 # Match the whole word (e.g., "breach")
        ["']?                     # Allow for an optional quote (e.g., "Breach" is...)
        \s* # Match any whitespace
        (?:is defined as|is|means|refers to) # Match common definition phrases
        \s* # Match any whitespace
        ([^.]+)                   # Capture group 1: Capture everything until the next period
        \.                        # Match the period that ends the sentence
    """
    
    match = re.search(pattern, text_to_search, re.IGNORECASE | re.VERBOSE)
    # --- *** END OF NEW REGEX *** ---

    return match.group(1).strip() if match else "Simplified explanation not found."