from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
import hashlib

from app.database import get_db

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_input(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# =========================
# REGISTER
# =========================
@router.post("/api/register")
def register(data: dict):
    try:
        conn = get_db()
        cur = conn.cursor()

        name = data.get("name")
        email = data.get("email")
        password_raw = data.get("password")
        role = data.get("role")

        if not name or not email or not password_raw or not role:
            raise HTTPException(status_code=400, detail="All fields required")

        safe_password = hash_input(password_raw)
        hashed_password = pwd_context.hash(safe_password)

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, role)
        )

        conn.commit()
        conn.close()

        return {"message": "Registration successful"}

    except Exception as e:
        print("REGISTER ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# LOGIN
# =========================
@router.post("/api/login")
def login(data: dict):
    try:
        conn = get_db()
        cur = conn.cursor()

        email = data.get("email")
        password = data.get("password")

        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()

        conn.close()

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        safe_password = hash_input(password)

        if pwd_context.verify(safe_password, user["password"]):
            return {
                "message": "Login successful",
                "user_id": user["id"],
                "name": user["name"],
                "role": user["role"]
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid password")

    except Exception as e:
        print("LOGIN ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))