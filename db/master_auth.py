# master_auth.py
# (CORRECTED - Removed conflicting init_master_db function)

import hashlib
import sqlite3
# --- MODIFIED: Added timezone ---
from datetime import datetime, timedelta, timezone 
import jwt
import secrets
import os
import re
import pandas as pd # <-- IMPORT FOR ADMIN FUNCTIONS

# --- NEW IMPORTS FOR GMAIL ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# --- END NEW IMPORTS ---


MASTER_DB_PATH = "db/master.db"

def _connect_master():
    """Establishes connection to the master database and enables foreign keys."""
    conn = sqlite3.connect(MASTER_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# -------------------------------------------------------------------
# --- DELETED init_master_db() FUNCTION ---
# This function belongs in master_db.py and was causing a conflict.
# -------------------------------------------------------------------

# --- JWT Secret Management ---
SECRET_KEY_FILE = "jwt.secret"
try:
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r") as f:
            SECRET_KEY = f.read().strip() # Read and strip potential whitespace
        if not SECRET_KEY: # Handle empty file case
            raise ValueError("Secret key file is empty.")
    else:
        SECRET_KEY = secrets.token_hex(32)
        with open(SECRET_KEY_FILE, "w") as f:
            f.write(SECRET_KEY)
        print(f"Generated new JWT secret key in {SECRET_KEY_FILE}")
except Exception as e:
    print(f"CRITICAL ERROR loading/generating JWT secret key: {e}")
    # Fallback to a default, less secure key ONLY for immediate running, NOT production
    SECRET_KEY = "your-fallback-secret-key-32-chars" # Replace if needed for testing, but fix file handling!
    print("WARNING: Using fallback JWT secret key. Please fix file permissions or path.")

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24
RESET_TOKEN_EXPIRY_MINUTES = 15

# --- Password Utilities ---
def hash_password(password: str) -> str:
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def is_strong_password(password: str) -> bool:
    """Checks if password meets complexity requirements."""
    if len(password) < 8: return False
    if not re.search("[a-z]", password): return False
    if not re.search("[A-Z]", password): return False
    if not re.search("[0-9]", password): return False
    if not re.search("[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password): return False
    return True

# --- JWT Utilities ---
def generate_jwt_token(email: str, account_id: int, is_admin: bool) -> str:
    """Generates a JWT token for the user."""
    payload = {
        "email": email,
        "account_id": account_id,
        "is_admin": is_admin,
        # --- MODIFIED: Use timezone-aware datetime ---
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str):
    """Verifies a JWT token. Returns payload or None."""
    try:
        # --- MODIFIED: Use timezone-aware decoding ---
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], leeway=timedelta(seconds=10))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# --- Account Management Functions ---

# Register new account (admin or tenant)
def register_account(email: str, password: str):
    """Registers a new user account (admin or regular tenant)."""
    # --- Input validation ---
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        # --- FIX: Added 'None' as the 5th return value ---
        return False, "Invalid email format.", None, None, None
    if not is_strong_password(password):
        return (
            False,
            "Password must be >= 8 chars with uppercase, lowercase, digit, and symbol.",
            None, None, None, # --- FIX: Added 'None' as the 5th return value ---
        )

    conn = None # Initialize conn outside try
    try:
        conn = _connect_master()
        c = conn.cursor()
        
        # --- NEW LOGIC: Check for Admin Email Tag ---
        is_admin = False
        
        # This is your "secret format"
        if "+admin@" in email.lower():
            is_admin = True
            # Remove the tag from the email before saving
            # "my-email+admin@gmail.com" becomes "my-email@gmail.com"
            email = email.replace("+admin@", "@").replace("+ADMIN@", "@")
            print(f"Admin tag found. Registering {email} as an admin.")
        
        # --- END NEW LOGIC ---

        # --- Check if email already exists ---
        # (This check must come AFTER we strip the tag)
        c.execute("SELECT id FROM accounts WHERE email=?", (email,))
        if c.fetchone():
            # --- FIX: Added 'None' as the 5th return value ---
            return False, "Email already registered.", None, None, None

        # --- Insert into accounts table ---
        pwd_hash = hash_password(password)
        c.execute(
            "INSERT INTO accounts (email, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (email, pwd_hash, int(is_admin), datetime.now()),
        )
        account_id = c.lastrowid # Get the ID of the newly created account

        # --- START FIX: Insert into tenants table IF it's NOT an admin account ---
        if not is_admin:
            tenant_name = email # Use email as the default tenant name, change if needed
            try:
                c.execute(
                    "INSERT INTO tenants (account_id, tenant_name) VALUES (?, ?)",
                    (account_id, tenant_name)
                )
            except sqlite3.IntegrityError:
                print(f"Warning: IntegrityError when adding account {account_id} to tenants table. Might already exist.")
                pass 
        # --- END FIX ---

        conn.commit() # Commit changes to both tables

        # --- Generate token and return success ---
        token = generate_jwt_token(email, account_id, bool(is_admin))
        return True, "Registration successful.", token, account_id, email

    except Exception as e:
        # --- Handle potential errors ---
        if conn:
            conn.rollback() # Rollback transaction on error
        print(f"Error during registration: {e}") # Log the error
        # --- FIX: Added 'None' as the 5th return value ---
        return False, f"An error occurred during registration.", None, None, None
    finally:
        # --- Ensure connection is closed ---
        if conn:
            conn.close()


# Login existing account with password verification
def login_account(email: str, password: str):
    """Logs in a user by verifying email and password hash."""
    conn = None
    try:
        conn = _connect_master()
        c = conn.cursor()
        pwd_hash = hash_password(password)
        # Verify against the master accounts table
        c.execute(
            "SELECT id, email, is_admin, password_hash FROM accounts WHERE email=?",
            (email,),
        )
        row = c.fetchone()
        # Check if user exists and password matches
        if not row or row[3] != pwd_hash:
            # --- FIX: Added 'False' as the 5th return value ---
            return False, "Invalid email or password.", None, None, False

        account_id, user_email, is_admin, _ = row # Unpack the row
        token = generate_jwt_token(user_email, account_id, bool(is_admin))
        return True, "Login successful.", token, account_id, bool(is_admin)
    except Exception as e:
        print(f"Error during login: {e}")
        # --- FIX: Added 'False' as the 5th return value ---
        return False, "An error occurred during login.", None, None, False
    finally:
        if conn:
            conn.close()


# ===================================================================
# --- PASSWORD RESET FUNCTION (REPLACED FOR GMAIL) ---
# ===================================================================
def request_password_reset_token(email: str, expires_in_minutes: int = RESET_TOKEN_EXPIRY_MINUTES):
    """
    Checks if user exists. If so, generates a *simple* token (not JWT),
    saves it to the DB, and sends it via GMAIL (smtplib).
    
    THIS IS FOR TESTING ONLY AND IS NOT RELIABLE.
    """
    conn = None
    try:
        conn = _connect_master()
        c = conn.cursor()
        c.execute("SELECT id FROM accounts WHERE email=?", (email,))
        user = c.fetchone()

        if not user:
            return False, "Email address not found.", None

        # 1. Generate a simple token
        token = secrets.token_urlsafe(16)
        expires = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        
        # 2. Save token to database
        c.execute(
            "UPDATE accounts SET reset_token=?, reset_token_expires=? WHERE email=?",
            (token, expires, email),
        )
        conn.commit()

        # 3. Get Gmail Credentials from .env file
        SENDER_EMAIL = os.environ.get("GMAIL_USER")
        SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
        
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            # Fallback for demo mode if key is missing
            print(f"Email sending not configured. Token for {email}: {token}")
            return True, f"Email sending not configured. Token for {email}", token

        # 4. Create the email content
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your ClauseEase AI Password Reset Token"
        message["From"] = f"ClauseEase AI <{SENDER_EMAIL}>"
        message["To"] = email
        
        # Create the HTML body
        html_content = f"""
        <html><body>
            <p>Hello,</p>
            <p>Here is your password reset token (valid for {expires_in_minutes} minutes):</p>
            <p style="background-color: #f4f4f4; padding: 10px; font-family: monospace;">{token}</p>
            <p>If you did not request this, please ignore this email.</p>
        </body></html>
        """
        message.attach(MIMEText(html_content, "html"))

        # 5. Send the email using smtplib
        try:
            # Connect to Google's SMTP server
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, message.as_string())
            server.close()
            
            # This will NOT show the token on the screen anymore
            return True, "Reset token has been sent to your email (check your spam folder).", None
        
        except Exception as e:
            # This will often fail due to Google's security
            print(f"Email sending failed: {e}")
            return False, f"Email sending failed (Google may have blocked it): {e}", None

    except Exception as e:
        print(f"Error requesting password reset: {e}")
        return False, f"An error occurred.", None
    finally:
        if conn:
            conn.close()
# ===================================================================
# --- END OF REPLACED FUNCTION ---
# ===================================================================


# Helper for parsing SQLite timestamps safely
def _parse_sqlite_ts(ts: str) -> datetime | None:
    """Safely parses SQLite timestamp strings."""
    if ts is None:
        return None
    # Add more formats if necessary
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except (ValueError, TypeError):
            continue
    try: # Fallback for ISO format
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


# Password reset with token verification
def reset_password_with_token(email: str, token: str, new_password: str):
    """Resets the password if the provided token is valid and not expired."""
    if not is_strong_password(new_password):
        return ( False, "New password does not meet complexity requirements.")

    conn = None
    try:
        conn = _connect_master()
        c = conn.cursor()
        c.execute(
            "SELECT reset_token_expires FROM accounts WHERE email=? AND reset_token=?",
            (email, token),
        )
        row = c.fetchone()
        if not row:
            return False, "Invalid or expired token."

        exp_raw = row[0]
        exp_dt = _parse_sqlite_ts(exp_raw)

        # Note: Your _parse_sqlite_ts function returns a naive datetime.
# We must make it timezone-aware to compare.
        if not exp_dt or exp_dt < datetime.now(timezone.utc).replace(tzinfo=None):
            # Clear expired token anyway
            c.execute("UPDATE accounts SET reset_token=NULL, reset_token_expires=NULL WHERE email=?", (email,))
            conn.commit()
            return False, "Token has expired."

        # Token is valid, update password and clear token
        new_hash = hash_password(new_password)
        c.execute(
            "UPDATE accounts SET password_hash=?, reset_token=NULL, reset_token_expires=NULL WHERE email=?",
            (new_hash, email),
        )
        conn.commit()
        return True, "Password reset successfully."
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False, "An error occurred during password reset."
    finally:
        if conn:
            conn.close()


# ===================================================================
# --- NEW ADMIN FUNCTIONS ---
# ===================================================================

def get_all_accounts_from_master():
    """Fetches all user accounts from the master.db for the admin panel."""
    conn = None
    try:
        conn = _connect_master()
        conn.row_factory = sqlite3.Row # Return dicts
        c = conn.cursor()
        c.execute("SELECT id, email, created_at, is_admin FROM accounts ORDER BY created_at DESC")
        rows = c.fetchall()
        return [dict(row) for row in rows] # Convert to list of dicts
    except Exception as e:
        print(f"Error in get_all_accounts_from_master: {e}")
        return [] # Return empty list on error
    finally:
        if conn:
            conn.close()

def get_table_from_master(table_name: str):
    """
    Safely fetches all data from a specified table in the master.db.
    Uses a whitelist to prevent SQL injection.
    """
    # Whitelist of allowed tables to prevent SQL injection
    ALLOWED_TABLES = ["accounts", "tenants"]
    
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Access to table '{table_name}' is not allowed.")

    conn = None
    try:
        conn = _connect_master()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # f-string is safe here because of the whitelist check above
        c.execute(f"SELECT * FROM {table_name}")
        
        rows = c.fetchall()
        # Convert to DataFrame for st.dataframe()
        return pd.DataFrame([dict(row) for row in rows]) 
    except Exception as e:
        print(f"Error in get_table_from_master({table_name}): {e}")
        return pd.DataFrame() # Return empty DataFrame on error
    finally:
        if conn:
            conn.close()
# Add this to the BOTTOM of db/master_auth.py

def get_account_details_by_email(email: str):
    """
    Fetches account details by email without a password.
    Used to log in a user verified by Google.
    """
    conn = None
    try:
        conn = _connect_master() # <-- USES THE CORRECT MASTER CONNECTION
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, email, is_admin FROM accounts WHERE email=?", (email,))
        row = c.fetchone()
        if row:
            return dict(row) # Returns {'id': 1, 'email': '...', 'is_admin': 0}
        return None
    except Exception as e:
        print(f"Error in get_account_details_by_email: {e}") # Log to console
        return None
    finally:
        if conn:
            conn.close()