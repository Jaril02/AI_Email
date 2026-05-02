import sqlite3

DB_NAME = "users.db"


# =========================
# INIT USERS TABLE
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT,
            role TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# CREATE USER
# =========================
def create_user(name, email, phone, password, role):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, password, role))

        conn.commit()
        conn.close()
        return True
    except:
        return False


# =========================
# GET USER
# =========================
def get_user_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "password": row[4],
            "role": row[5],
        }
    return None


# =========================
# CREATE SENDERS TABLE
# =========================
def create_senders_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS senders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            organization_name TEXT,
            email TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# ADD SENDER
# =========================
def add_sender(user_id, name, org_name, email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO senders (user_id, name, organization_name, email, password)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, org_name, email, password))

    conn.commit()
    conn.close()


# =========================
# GET SENDERS (ONLY EMAIL LIST)
# =========================
def get_senders(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, email FROM senders WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    conn.close()

    return [{"id": r[0], "email": r[1]} for r in rows]


# =========================
# GET SINGLE SENDER
# =========================
def get_sender_by_id(sender_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM senders WHERE id = ?", (sender_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "organization_name": row[3],
            "email": row[4],
            "password": row[5],
        }
    return None