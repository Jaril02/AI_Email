import json
import requests
import redis
import os
from dotenv import load_dotenv
from app.excel_utils import parse_excel, detect_email_column
from app.email_service import send_email_smtp, load_smtp_settings
from test import check_bounces

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER")

r = redis.Redis(host='localhost', port=6379, db=0)

# Load flow
with open("chat.json", "r") as f:
    FLOW = json.load(f)


# ---------------- STATE ---------------- #

def get_state(session_id):
    state = r.get(f"state:{session_id}")
    if state:
        return json.loads(state)
    return {
        "stage": "start",
        "excel_uploaded": False,
        "validated": False,
        "sending": False
    }


def save_state(session_id, state):
    r.set(f"state:{session_id}", json.dumps(state), ex=3600)


# ---------------- LLM DECISION ---------------- #

def decide_action(user_input, stage):
    prompt = f"""
    You are an AI assistant controlling an email automation system.

    Current stage: {stage}

    Rules:
    - Do NOT repeat the same action if already completed
    - Move forward in workflow

    Valid actions:
    start
    upload_excel
    process_excel
    send_emails
    check_status

    If unsure:
    {{ "action": "help" }}

    User input: "{user_input}"

    Return ONLY JSON:
    {{ "action": "" }}
    """

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50
        }
    )

    try:
        return json.loads(response.json()["choices"][0]["message"]["content"])
    except:
        return {"action": "help"}


# ---------------- TOOL MOCKS ---------------- #

def process_excel(state):
    rows = state.get("rows", [])

    email_column = detect_email_column(rows)

    valid = 0
    invalid = 0

    for row in rows:
        email = row.get(email_column, "")
        if "@" in str(email):
            valid += 1
        else:
            invalid += 1

    return {"valid": valid, "invalid": invalid}

def send_emails():
    return {"sent": 100}


def check_bounces():
    return {"failed": 5}


# ---------------- MAIN HANDLER ---------------- #
def handle_chat(user_input, session_id, app_state):

    state = get_state(session_id)
    stage = state["stage"]

    text = user_input.lower()

    if "start" in text:
        action = "start"

    elif "upload" in text:
        action = "upload_excel"

    elif "process" in text:
        action = "process_excel"

    elif "send" in text:
        action = "send_emails"

    elif "status" in text or "bounce" in text:
        action = "check_status"

    else:
        decision = decide_action(user_input, stage)
        action = decision.get("action", "help")

    message = ""

    # -------- ACTION HANDLING -------- #

    if action == "start" and state["stage"] != "start":
        action = "help"
    elif action == "start":
        state["stage"] = "upload_excel"
        message = "Please upload your Excel file."

    elif action == "upload_excel":
        state["excel_uploaded"] = True
        state["stage"] = "process_excel"
        message = "Excel received. Processing now..."

    elif action == "process_excel":
        result = process_excel(state)
        state["validated"] = True
        state["stage"] = "ready_to_send"

        message = f"I found {result['valid']} valid emails and {result['invalid']} invalid ones."

    elif action == "send_emails":
        result = send_emails()
        state["sending"] = True
        state["stage"] = "tracking"

        message = f"Sent {result['sent']} emails."

    elif action == "check_status":
        result = check_bounces()
        state["stage"] = "done"

        message = f"{result['failed']} emails failed (bounced)."

    else:
        message = "You can say things like: start, upload excel, send emails, check status."

    save_state(session_id, state)
    print("USER:", user_input)
    print("STAGE:", stage)
    print("ACTION:", action)

    return {
        "stage": state["stage"],
        "message": message,
        "state": state
    }
    