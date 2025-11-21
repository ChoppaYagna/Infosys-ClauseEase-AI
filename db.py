# db.py - COMPLETE DATABASE MODULE
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

def get_db_connection(tenant_db: str) -> sqlite3.Connection:
    """
    Create a database connection to the SQLite database.
    
    Args:
        tenant_db: Path to the database file
        
    Returns:
        SQLite connection object
    """
    try:
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(tenant_db)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        conn = sqlite3.connect(tenant_db)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to database: {e}")

def initialize_database(tenant_db: str) -> bool:
    """
    Initialize the database with required tables.
    
    Args:
        tenant_db: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        # Chat sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                chat_history TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT,
                file_size INTEGER,
                processed_text TEXT,
                simplification_level TEXT,
                model_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        ''')
        
        # Glossary terms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS glossary_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                term TEXT NOT NULL,
                definition TEXT NOT NULL,
                category TEXT,
                examples TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_id, term)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, preference_key)
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def load_chat_history(tenant_db: str, document_id: str, user_id: str) -> List[tuple]:
    """
    Load chat history for a specific document and user.
    
    Args:
        tenant_db: Path to the database file
        document_id: Unique identifier for the document
        user_id: Unique identifier for the user
        
    Returns:
        List of tuples (author, message)
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chat_history FROM chat_sessions 
            WHERE document_id = ? AND user_id = ? 
            ORDER BY updated_at DESC LIMIT 1
        ''', (document_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            try:
                chat_data = json.loads(result[0])
                # Convert to list of tuples if it's stored as list of lists
                if chat_data and isinstance(chat_data, list):
                    if isinstance(chat_data[0], list):
                        return [(item[0], item[1]) for item in chat_data]
                    else:
                        return chat_data
                return []
            except json.JSONDecodeError:
                return []
        else:
            return []
            
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []

def save_chat_history(tenant_db: str, document_id: str, user_id: str, chat_history: List[tuple]) -> bool:
    """
    Save chat history for a specific document and user.
    
    Args:
        tenant_db: Path to the database file
        document_id: Unique identifier for the document
        user_id: Unique identifier for the user
        chat_history: List of tuples (author, message)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        # Convert chat history to JSON string
        chat_json = json.dumps(chat_history)
        
        # Check if chat session already exists
        cursor.execute('''
            SELECT id FROM chat_sessions 
            WHERE document_id = ? AND user_id = ?
        ''', (document_id, user_id))
        
        existing_session = cursor.fetchone()
        
        if existing_session:
            # Update existing session
            cursor.execute('''
                UPDATE chat_sessions 
                SET chat_history = ?, updated_at = CURRENT_TIMESTAMP
                WHERE document_id = ? AND user_id = ?
            ''', (chat_json, document_id, user_id))
        else:
            # Create new session
            cursor.execute('''
                INSERT INTO chat_sessions (document_id, user_id, chat_history)
                VALUES (?, ?, ?)
            ''', (document_id, user_id, chat_json))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving chat history: {e}")
        return False

def save_document_metadata(tenant_db: str, document_data: Dict[str, Any]) -> bool:
    """
    Save document metadata to the database.
    
    Args:
        tenant_db: Path to the database file
        document_data: Dictionary containing document metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (document_id, user_id, title, file_name, file_size, processed_text, simplification_level, model_used, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            document_data.get('document_id'),
            document_data.get('user_id'),
            document_data.get('title', 'Untitled Document'),
            document_data.get('file_name'),
            document_data.get('file_size'),
            document_data.get('processed_text', ''),
            document_data.get('simplification_level', 'standard'),
            document_data.get('model_used', 'gpt-3.5-turbo')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving document metadata: {e}")
        return False

def load_document_metadata(tenant_db: str, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load document metadata from the database.
    
    Args:
        tenant_db: Path to the database file
        document_id: Unique identifier for the document
        user_id: Unique identifier for the user
        
    Returns:
        Dictionary containing document metadata or None if not found
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM documents 
            WHERE document_id = ? AND user_id = ?
        ''', (document_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        else:
            return None
            
    except Exception as e:
        print(f"Error loading document metadata: {e}")
        return None

def get_user_documents(tenant_db: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all documents for a specific user.
    
    Args:
        tenant_db: Path to the database file
        user_id: Unique identifier for the user
        
    Returns:
        List of document dictionaries
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT document_id, title, file_name, file_size, created_at, processed_at
            FROM documents 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
            
    except Exception as e:
        print(f"Error getting user documents: {e}")
        return []

def get_glossary_terms(tenant_db: str, tenant_id: str = "default") -> Dict[str, str]:
    """
    Get glossary terms for a specific tenant.
    
    Args:
        tenant_db: Path to the database file
        tenant_id: Tenant identifier
        
    Returns:
        Dictionary of terms and definitions
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT term, definition FROM glossary_terms 
            WHERE tenant_id = ?
        ''', (tenant_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}
        
    except Exception as e:
        print(f"Error loading glossary terms: {e}")
        return {}

def save_glossary_term(tenant_db: str, tenant_id: str, term: str, definition: str, category: str = None) -> bool:
    """
    Save a glossary term to the database.
    
    Args:
        tenant_db: Path to the database file
        tenant_id: Tenant identifier
        term: The term to save
        definition: Definition of the term
        category: Optional category for the term
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO glossary_terms 
            (tenant_id, term, definition, category)
            VALUES (?, ?, ?, ?)
        ''', (tenant_id, term, definition, category))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving glossary term: {e}")
        return False

def delete_chat_history(tenant_db: str, document_id: str, user_id: str) -> bool:
    """
    Delete chat history for a specific document and user.
    
    Args:
        tenant_db: Path to the database file
        document_id: Unique identifier for the document
        user_id: Unique identifier for the user
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM chat_sessions 
            WHERE document_id = ? AND user_id = ?
        ''', (document_id, user_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error deleting chat history: {e}")
        return False

def get_user_preference(tenant_db: str, user_id: str, preference_key: str) -> Optional[str]:
    """
    Get a user preference from the database.
    
    Args:
        tenant_db: Path to the database file
        user_id: Unique identifier for the user
        preference_key: The preference key to retrieve
        
    Returns:
        Preference value or None if not found
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_value FROM user_preferences 
            WHERE user_id = ? AND preference_key = ?
        ''', (user_id, preference_key))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error getting user preference: {e}")
        return None

def save_user_preference(tenant_db: str, user_id: str, preference_key: str, preference_value: str) -> bool:
    """
    Save a user preference to the database.
    
    Args:
        tenant_db: Path to the database file
        user_id: Unique identifier for the user
        preference_key: The preference key to save
        preference_value: The preference value to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences 
            (user_id, preference_key, preference_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, preference_key, preference_value))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving user preference: {e}")
        return False

def get_chat_statistics(tenant_db: str, user_id: str) -> Dict[str, Any]:
    """
    Get chat statistics for a user.
    
    Args:
        tenant_db: Path to the database file
        user_id: Unique identifier for the user
        
    Returns:
        Dictionary with chat statistics
    """
    try:
        # Initialize database first
        initialize_database(tenant_db)
        
        conn = get_db_connection(tenant_db)
        cursor = conn.cursor()
        
        # Total chat sessions
        cursor.execute('''
            SELECT COUNT(*) as total_sessions FROM chat_sessions 
            WHERE user_id = ?
        ''', (user_id,))
        total_sessions = cursor.fetchone()[0]
        
        # Recent activity
        cursor.execute('''
            SELECT MAX(updated_at) as last_activity FROM chat_sessions 
            WHERE user_id = ?
        ''', (user_id,))
        last_activity = cursor.fetchone()[0]
        
        # Documents with chat history
        cursor.execute('''
            SELECT COUNT(DISTINCT document_id) as active_documents FROM chat_sessions 
            WHERE user_id = ?
        ''', (user_id,))
        active_documents = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'last_activity': last_activity,
            'active_documents': active_documents
        }
        
    except Exception as e:
        print(f"Error getting chat statistics: {e}")
        return {
            'total_sessions': 0,
            'last_activity': None,
            'active_documents': 0
        }

# Initialize default glossary terms
def initialize_default_glossary(tenant_db: str):
    """Initialize default legal glossary terms."""
    default_terms = {
        "Confidentiality": "A legal agreement that protects sensitive information from being disclosed to unauthorized parties.",
        "Indemnification": "A contractual obligation where one party agrees to compensate another for losses or damages.",
        "Jurisdiction": "The official power to make legal decisions and judgments, often specifying which court or legal system governs the agreement.",
        "Liability": "Legal responsibility for one's actions or obligations, often involving financial consequences.",
        "Termination": "The act of ending a contract or agreement before its natural expiration date.",
        "Arbitration": "A method of dispute resolution where parties agree to settle their dispute outside of court.",
        "Force Majeure": "A clause that frees both parties from liability or obligation when an extraordinary event occurs.",
        "Warranty": "A guarantee or promise provided by one party to another regarding the condition or performance of something.",
        "Amendment": "A formal change or modification made to a legal document or contract.",
        "Breach": "The violation of a legal obligation, duty, or law, typically resulting in legal action."
    }
    
    for term, definition in default_terms.items():
        save_glossary_term(tenant_db, "default", term, definition, "Legal")