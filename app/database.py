import sqlite3

DB_NAME = "users.db"


# =========================
# DB CONNECTION (Reusable)
# =========================
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 🔥 important for dict-like access
    return conn


# =========================
# INIT USERS TABLE
# =========================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# CREATE USER
# =========================
def create_user(name, email, phone, password, role):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, password, role))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False  # email already exists

    finally:
        conn.close()


# =========================
# GET USER BY EMAIL
# =========================
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)  # 🔥 cleaner than manual mapping
    return None


# =========================
# CREATE SENDERS TABLE
# =========================
def create_senders_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS senders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            organization_name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# =========================
# ADD SENDER
# =========================
def add_sender(user_id, name, org_name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO senders (user_id, name, organization_name, email, password)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, org_name, email, password))

    conn.commit()
    conn.close()


# =========================
# GET SENDERS (LIST)
# =========================
def get_senders(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, organization_name, email
        FROM senders
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]  # 🔥 clean output


# =========================
# GET SINGLE SENDER
# =========================
def get_sender_by_id(sender_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM senders WHERE id = ?", (sender_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None