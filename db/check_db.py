import sqlite3

db_path = "db/master.db"  # Change path for different database files

def get_table_names(conn):
    return [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]

def print_table_structure(conn, table):
    print(f"\n-- {table} --")
    columns = conn.execute(f"PRAGMA table_info({table});").fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

def print_all_rows(conn, table):
    rows = conn.execute(f"SELECT * FROM {table};").fetchall()
    print(f"Data ({len(rows)} rows):")
    for row in rows:
        print(row)

if __name__ == "__main__":
    conn = sqlite3.connect(db_path)
    tables = get_table_names(conn)
    for table in tables:
        print_table_structure(conn, table)
        print_all_rows(conn, table)
    conn.close()
import sqlite3
import os

def inspect_tenant_db(email):
    # Sanitize the email to match tenant DB filename pattern in your code
    safe_email = email.replace('@', '_at_').replace('.', '_dot_')
    db_path = os.path.join("db/tenants", f"{safe_email}.db")

    if not os.path.exists(db_path):
        print(f"Tenant DB not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print(f"Tables in {db_path}: {tables}")

    for table in tables:
        print(f"\n-- {table} --")
        columns = conn.execute(f"PRAGMA table_info({table});").fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        rows = conn.execute(f"SELECT * FROM {table} LIMIT 10;").fetchall()
        print(f"Sample rows (up to 10):")
        for row in rows:
            print(row)

    conn.close()

# Example: replace below with tenant email to inspect
inspect_tenant_db("ashwathyadmin123@gmail.com")
