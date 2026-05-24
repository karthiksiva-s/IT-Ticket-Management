# ============================================================
# database.py — Database connection and table creation
# We use SQLite (a simple file-based database, no server needed)
# ============================================================

import sqlite3

# The database file will be created in the backend folder
DB_PATH = "tickets.db"


def get_connection():
    """
    Opens a connection to the SQLite database.
    'check_same_thread=False' is needed for FastAPI's async handling.
    'Row' factory lets us access columns by name (like dict).
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns as: row["column_name"]
    return conn


def create_tables():
    """
    Creates the database tables if they don't already exist.
    This runs every time the server starts — safe to run multiple times.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------------------------------------
    # USERS TABLE
    # Stores both regular users and admins
    # role = 'user' or 'admin'
    # -------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    # -------------------------------------------------------
    # TICKETS TABLE
    # Stores all support tickets
    # -------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,       -- e.g., TKT-20240101-0001
            employee_name TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            asset_id TEXT NOT NULL,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,               -- Low, Medium, High
            status TEXT NOT NULL DEFAULT 'Open',  -- Open, In Progress, Closed, Canceled
            created_date TEXT NOT NULL,           -- Stored as ISO date string
            admin_response TEXT,                  -- Admin's reply (nullable)
            cancel_reason TEXT,                   -- User's cancel reason (nullable)
            created_by INTEGER NOT NULL,          -- FK → users.id
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # -------------------------------------------------------
    # Seed a default admin account (only if it doesn't exist)
    # Username: admin | Password: admin123
    # -------------------------------------------------------
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    conn.commit()
    conn.close()
    print("✅ Database tables ready.")