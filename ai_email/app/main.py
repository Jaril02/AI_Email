from fastapi import FastAPI, UploadFile, File
from typing import List
import io

from app.excel_utils import read_excel
from app.ai_client import enhance_email

app = FastAPI()

users_data = []
attachments = []


@app.get("/")
def home():
    return {"status": "Backend running"}


# ---------------------------
# Upload Excel
# ---------------------------
@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    global users_data

    try:
        content = await file.read()
        users_data = read_excel(io.BytesIO(content))

        return {
            "rows_count": len(users_data),
            "columns": list(users_data[0].keys()) if users_data else [],
            "first_name_column": "Name"
        }

    except Exception as e:
        return {"detail": str(e)}


# ---------------------------
# Upload Attachments
# ---------------------------
@app.post("/api/upload-attachments")
async def upload_attachments(files: List[UploadFile] = File(...)):
    global attachments

    attachments = []

    for f in files:
        content = await f.read()
        attachments.append({
            "filename": f.filename,
            "content": content
        })

    return {"attachments": [a["filename"] for a in attachments]}


# ---------------------------
# Generate Message
# ---------------------------
@app.post("/api/generate-message")
def generate_message(data: dict):
    objective = data.get("objective", "")

    msg = f"Hi {{first_name}},\n\n{objective}\n\nRegards,\nTeam"

    return {"message": msg}


# ---------------------------
# Enhance Message
# ---------------------------
@app.post("/api/enhance-message")
def enhance_message(data: dict):
    text = data.get("message", "")
    return {"message": enhance_email(text)}


# ---------------------------
# Preview
# ---------------------------
@app.post("/api/preview")
def preview(data: dict):
    template = data.get("message_template", "")
    limit = data.get("limit", 5)

    result = []

    for user in users_data[:limit]:
        name = user.get("Name", "User")
        msg = template.replace("{first_name}", name)

        result.append({
            "recipient": user,
            "message": msg
        })

    return {"count": len(result), "previews": result}


# ---------------------------
# Send (Demo)
# ---------------------------
@app.post("/api/send")
def send(data: dict):
    return {
        "message": "Emails processed (demo)",
        "total_recipients": len(users_data)
    }