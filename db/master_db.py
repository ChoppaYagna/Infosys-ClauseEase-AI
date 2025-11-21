import sqlite3
import os
from datetime import datetime

MASTER_DB_PATH = "db/master.db"

def _connect_master():
    conn = sqlite3.connect(MASTER_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_master_db():
    os.makedirs(os.path.dirname(MASTER_DB_PATH), exist_ok=True)
    conn = _connect_master()
    c = conn.cursor()
    # Accounts table: includes admin and tenant (user) accounts
    c.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reset_token TEXT,
        reset_token_expires TIMESTAMP
    );
    """)
    # Tenants mapping table
    c.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        tenant_name TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    );
    """)
    conn.commit()
    conn.close()

def get_account_password_hash(account_id):
    conn = _connect_master()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM accounts WHERE id = ?", (account_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "dummy_hash"

def get_admin_accounts():
    conn = _connect_master()
    c = conn.cursor()
    c.execute("SELECT id, email, created_at FROM accounts WHERE is_admin = 1")
    admins = c.fetchall()
    conn.close()
    return admins

def get_all_tenants():
    conn = _connect_master()
    c = conn.cursor()
    c.execute("SELECT * FROM tenants;")
    rows = c.fetchall()
    conn.close()
    return rows
