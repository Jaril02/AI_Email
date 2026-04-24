from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from torch import mode
from typing import List
from app.ai_client import API_KEY, enhance_email
# from app.chatbot_engine import handle_chat
import hashlib

from test import check_bounces
import os
# from app.ai_client import AIClient
from app.email_service import load_smtp_settings, send_email_smtp
from app.excel_utils import (
    detect_email_column,
    detect_first_name_column,
    parse_excel,
    personalize_message,
)
from app.schemas import EnhanceRequest, GenerateRequest, PreviewRequest, SendRequest

app = FastAPI(title="AI Email Automation Agent")

# ai_client = AIClient()

# In-memory session data for demo/simple local usage.
state: dict[str, object] = {
    "rows": [],
    "first_name_column": None,
    "email_column": None,
    "attachments": [],
    "send_stats": {
        "total_attempts": 0,
        "delivered": 0,
        "failed": 0,
        "skipped": 0,
    },
    "last_batch": None,
}


@app.get("/")
async def root() -> dict[str, object]:
    """API-only backend; use Streamlit for the UI (`streamlit run streamlit_app.py`)."""
    return {
        "service": "AI Email Automation Agent",
        "docs": "/docs",
        # "ai_enabled": ai_client.enabled,
        "frontend": "streamlit run streamlit_app.py",
    }


@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Upload a valid Excel file (.xlsx or .xls).")

    content = await file.read()
    rows = parse_excel(content)
    first_name_column = detect_first_name_column(rows)

    email_column = detect_email_column(rows)

    state["rows"] = rows
    state["first_name_column"] = first_name_column
    state["email_column"] = email_column

    return {
        "success": True,
        "rows_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "first_name_column": first_name_column,
        "email_column": email_column,
    }


@app.post("/api/upload-attachments")
# async def upload_attachments(files: list[UploadFile] = File(...)) -> dict[str, object]:
#     names = [f.filename for f in files]
#     state["attachment_names"] = names
#     return {"success": True, "attachments": names}

async def upload_attachments(files: List[UploadFile] = File(...)):
    attachments = []

    for f in files:
        content = await f.read()
        attachments.append({
            "filename": f.filename,
            "content": content
        })
    state["attachments"] = attachments
    return {"attachments": [a["filename"] for a in attachments]}


# @app.post("/api/generate-message")
# async def generate_message(payload: GenerateRequest) -> dict[str, object]:
#     prompt = (
#         "Write an outreach email template with a friendly professional tone. "
#         "Use {first_name} for personalization, keep it under 150 words.\n\n"
#         f"Objective:\n{payload.objective}"
#     )
#     content = await ai_client.generate(prompt)
#     return {"success": True, "message": content}

@app.post("/api/generate-message")
def generate_message(data: dict):
    objective = data.get("objective", "")

    msg = f"Hi {{first_name}},\n\n{objective}\n\nRegards,\nTeam"

    return {"message": msg}


# @app.post("/api/enhance-message")
# async def enhance_message(payload: EnhanceRequest) -> dict[str, object]:
#     prompt = (
#         "Improve this email message for clarity and engagement while keeping the same intent. "
#         "Preserve placeholders like {first_name} and any {column_name} tags.\n\n"
#         f"Current message:\n{payload.message}"
#     )
#     content = await ai_client.generate(prompt)
#     return {"success": True, "message": content}

@app.post("/api/enhance-message")
def enhance_message(data: dict):
    text = data.get("message", "")
    
    return {"message": enhance_email(text)}
    


@app.post("/api/preview")
async def preview_messages(payload: PreviewRequest) -> dict[str, object]:
    rows = state.get("rows", [])
    if not rows:
        raise HTTPException(status_code=400, detail="Upload Excel before preview.")

    first_name_column = state.get("first_name_column")
    previews = []
    for row in rows[: payload.limit]:
        previews.append(
            {
                "recipient": row,
                "message": personalize_message(payload.message_template, row, first_name_column),
            }
        )

    return {"success": True, "count": len(previews), "previews": previews}


def _record_send_result(stats: dict[str, int], status: str) -> None:
    stats["total_attempts"] += 1
    if status == "delivered":
        stats["delivered"] += 1
    elif status == "bounced" or status == "failed":
        stats["failed"] += 1
    else:
        stats["skipped"] += 1




@app.get("/api/bounces")
def get_bounces():
    imap_host = os.getenv("IMAP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not imap_host or not user or not password:
        return {"error": "IMAP config missing"}

    results = check_bounces(imap_host, user, password)

    return {
        "success": True,
        "count": len(results),
        "bounces": results
    }

@app.post("/api/send")
async def send_messages(payload: SendRequest) -> dict[str, object]:
    rows = state.get("rows", [])
    if not rows:
        raise HTTPException(status_code=400, detail="Upload Excel before send.")

    first_name_column = state.get("first_name_column")
    email_column = state.get("email_column")
    stats: dict[str, int] = state["send_stats"]  # type: ignore[assignment]
    smtp = load_smtp_settings()
    print("SMTP CONFIG:", smtp)   # 👈 ADD THIS
    mode = "smtp" if smtp else "demo"
    print("MODE:", mode)          # 👈 ADD THIS

    results: list[dict[str, Any]] = []
    attachments = state.get("attachments", [])
    print("ATTACHMENTS:", attachments)  # debug

    for row in rows:
        if not email_column:
            results.append(
                {
                    "email": None,
                    "status": "skipped",
                    "detail": "No email column detected in Excel. Add a column named email.",
                }
            )
            _record_send_result(stats, "skipped")
            continue

        to_addr = str(row.get(email_column, "")).strip()
        if not to_addr:
            results.append({"email": None, "status": "skipped", "detail": "Empty email cell"})
            _record_send_result(stats, "skipped")
            continue

        body = personalize_message(payload.message_template, row, first_name_column)

        if smtp:
            try:
                send_email_smtp(to_addr, payload.subject, body, smtp,attachments)
                results.append(
                    {
                        "email": to_addr,
                        "status": "delivered",
                        "detail": "Accepted by SMTP server",
                    }
                )
                _record_send_result(stats, "delivered")
            except Exception as exc:  # noqa: BLE001 — surface last-mile errors to UI
                results.append(
                    {
                        "email": to_addr,
                        "status": "failed",
                        "detail": str(exc),
                    }
                )
                _record_send_result(stats, "failed")
        else:
            results.append(
                {
                    "email": to_addr,
                    "status": "delivered",
                    "detail": "Simulated (set SMTP_HOST and SMTP_FROM for real send)",
                }
            )
            _record_send_result(stats, "delivered")
    time.sleep(10)

    bounces = check_bounces()

    bounced_emails = {b["email"] for b in bounces if b.get("email")}
    for r in results:
        if r["email"] in bounced_emails:
            r["status"] = "bounced"
            r["detail"] = "Email bounced (invalid or rejected)"
    bounce_count = len(bounced_emails)
    delivered_count = sum(1 for r in results if r["status"] == "delivered")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    bounced_count = sum(1 for r in results if r["status"] == "bounced")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    state["last_batch"] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "subject": payload.subject,
        "mode": mode,
        "total": len(results), 
        "delivered": delivered_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "bounced": bounced_count,
        "bounced_emails": list(bounced_emails),
        "results": results, 
    }
    

    last = state["last_batch"]

    return {
        "success": True,
        "message": (
            f"Sent via SMTP "
            f"({last['delivered']} delivered, {last['failed']} failed, "
            f"{last['bounced']} bounced, {last['skipped']} skipped)."
            if smtp
            else f"Demo send complete ({last['delivered']} simulated delivered, {last['skipped']} skipped)."
        ),
        "total_recipients": len(rows),
        "subject": payload.subject,
        "attachments": state.get("attachment_names", []),
        "mode": mode,
        "last_batch": last,
        # "cumulative": dict(state["send_stats"]),
    }


@app.get("/api/send-status")
async def send_status() -> dict[str, object]:
    """Cumulative send counts and last batch detail for the status bar."""
    stats = state.get("send_stats", {})
    smtp = load_smtp_settings()
    return {
        "success": True,
        "last_batch": state.get("last_batch"),
        "smtp_configured": smtp is not None,
        "delivery_note": (
            "SMTP success means your server accepted the message for delivery. "
            "Inbox placement and opens are not tracked unless you add webhooks (e.g. SES, SendGrid)."
            if smtp
            else "Demo mode: counts mark simulated handoff. Set SMTP_* env vars for real sending."
        ),
    }

# @app.get("/chat")
# def chat(query: str):

#     session_id = "user1" 
#     response = handle_chat(query, session_id, state)

#     return response
