from __future__ import annotations

from fastapi import FastAPI, HTTPException, File, UploadFile
from typing import List, Any
import hashlib
import re

# =========================
# DATABASE
# =========================
from app.database import (
    init_db,
    create_user,
    get_user_by_email,
    create_senders_table,
    add_sender,
    get_senders,
    get_sender_by_id
)

# =========================
# EXISTING MODULES (UNCHANGED)
# =========================
from app.ai_client import enhance_email
from app.email_service import load_smtp_settings, send_email_smtp
from app.excel_utils import (
    detect_email_column,
    detect_first_name_column,
    parse_excel,
    personalize_message,
)
from app.schemas import PreviewRequest, SendRequest

# =========================
# INIT APP
# =========================
app = FastAPI(title="AI Email Automation Agent")

init_db()
create_senders_table()

# =========================
# PASSWORD HASH
# =========================
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


# =========================
# AUTH APIs
# =========================
@app.post("/api/register")
def register(data: dict):
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    role = data.get("role", "")
@app.get("/api/send-status")
def send_status():
    return {
        "success": True,
        "last_batch": {
            "total": 0,
            "delivered": 0,
            "failed": 0,
            "skipped": 0,
            "bounced": 0
        }
    }
    # VALIDATION
    if len(name) < 3:
        raise HTTPException(400, "Name must be at least 3 characters")

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise HTTPException(400, "Invalid email")

    if not phone.isdigit() or len(phone) != 10:
        raise HTTPException(400, "Phone must be 10 digits")

    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    if role not in ["individual", "organizational"]:
        raise HTTPException(400, "Invalid role")

    hashed = hash_password(password)

    if not create_user(name, email, phone, hashed, role):
        raise HTTPException(400, "Email already exists")

    return {"message": "Registration successful"}


@app.post("/api/login")
def login(data: dict):
    email = data.get("email", "").strip()
    password = data.get("password", "")

    user = get_user_by_email(email)

    if not user:
        raise HTTPException(400, "User not found")

    if hash_password(password) != user["password"]:
        raise HTTPException(400, "Invalid password")

    return {
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }


# =========================
# GLOBAL STATE
# =========================
state: dict[str, Any] = {
    "rows": [],
    "first_name_column": None,
    "email_column": None,
    "attachments": [],
    "active_sender": None,   # 🔥 important
}


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"message": "Backend running"}


# =========================
# 🔥 SENDER APIs
# =========================

@app.post("/api/senders/add")
def api_add_sender(data: dict):
    user_id = data.get("user_id")
    name = data.get("name")
    org = data.get("organization_name")
    email = data.get("email")
    password = data.get("password")

    if not all([user_id, name, org, email, password]):
        raise HTTPException(400, "All fields required")

    # email validation
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise HTTPException(400, "Invalid email format")

    add_sender(user_id, name, org, email, password)

    return {"message": "Sender added"}


@app.get("/api/senders/{user_id}")
def api_get_senders(user_id: int):
    return {"senders": get_senders(user_id)}


@app.post("/api/senders/select")
def select_sender(data: dict):
    sender_id = data.get("sender_id")

    sender = get_sender_by_id(sender_id)

    if not sender:
        raise HTTPException(404, "Sender not found")

    state["active_sender"] = sender

    return {
        "message": "Sender selected",
        "active_email": sender["email"]
    }


# =========================
# FILE UPLOAD
# =========================
@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    content = await file.read()

    rows = parse_excel(content)

    state["rows"] = rows
    state["first_name_column"] = detect_first_name_column(rows)
    state["email_column"] = detect_email_column(rows)

    return {"rows_count": len(rows)}


@app.post("/api/upload-attachments")
async def upload_attachments(files: List[UploadFile] = File(...)):
    attachments = []

    for f in files:
        content = await f.read()
        attachments.append({
            "filename": f.filename,
            "content": content
        })

    state["attachments"] = attachments

    return {"files": [f["filename"] for f in attachments]}


# =========================
# MESSAGE
# =========================
@app.post("/api/generate-message")
def generate_message(data: dict):
    objective = data.get("objective", "")
    return {
        "message": f"Hi {{first_name}},\n\n{objective}\n\nRegards,\nTeam"
    }


@app.post("/api/enhance-message")
def enhance_message(data: dict):
    return {"message": enhance_email(data.get("message", ""))}


@app.post("/api/preview")
def preview(payload: PreviewRequest):
    if not state["rows"]:
        raise HTTPException(400, "Upload Excel first")

    previews = []

    for row in state["rows"][:payload.limit]:
        msg = personalize_message(
            payload.message_template,
            row,
            state["first_name_column"]
        )
        previews.append({"message": msg})

    return {"previews": previews}


# =========================
# SEND EMAIL (MULTI-SENDER)
# =========================
@app.post("/api/send")
def send(payload: SendRequest):

    if not state["rows"]:
        raise HTTPException(400, "Upload Excel first")

    active = state.get("active_sender")

    # 🔥 USE SELECTED SENDER
    if active:
        smtp = {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": active["email"],
            "password": active["password"],
        }
    else:
        smtp = load_smtp_settings()

    for row in state["rows"]:
        email = row.get(state["email_column"])
        if not email:
            continue

        body = personalize_message(
            payload.message_template,
            row,
            state["first_name_column"]
        )

        try:
            send_email_smtp(
                email,
                payload.subject,
                body,
                smtp,
                state["attachments"]
            )
        except Exception as e:
            print("ERROR:", e)

    return {"message": "Emails sent successfully"}