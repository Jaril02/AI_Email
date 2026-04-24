import json
from typing import Any

import requests
import streamlit as st


st.set_page_config(page_title="AI Email Automation Agent", layout="wide")
st.title("AI Agent for Email Automation")

if "message" not in st.session_state:
    st.session_state.message = ""
if "preview" not in st.session_state:
    st.session_state.preview = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  


def chat_api(message: str):
    try:
        response = requests.get(
            f"{api_base_url()}/chat",
            params={"query": message},
            timeout=60
        )
        return response.json()
    except Exception:
        return {"message": "Error connecting to chatbot"}

def api_base_url() -> str:
    return st.session_state.get("api_base_url", "http://127.0.0.1:8000")


def get_json(endpoint: str) -> dict[str, Any] | None:
    try:
        response = requests.get(f"{api_base_url()}{endpoint}", timeout=60)
        if response.status_code >= 400:
            return None
        return response.json()
    except OSError:
        return None


def post_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{api_base_url()}{endpoint}", json=payload, timeout=60)
    data = response.json()
    if response.status_code >= 400:
        raise RuntimeError(data.get("detail", "Request failed"))
    return data


with st.sidebar:
    st.header("Backend")
    st.session_state.api_base_url = st.text_input("FastAPI URL", value=api_base_url())
    st.caption("Run backend first: uvicorn app.main:app --reload")

send_status = get_json("/api/send-status")
if send_status and send_status.get("success"):
    # cum = send_status.get("cumulative", {})
    last = send_status.get("last_batch") or {}
    st.subheader("Send status")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total", last.get("total", 0))
    with m2:
        st.metric("Delivered", last.get("delivered", 0))
    with m3:
        st.metric("Failed", last.get("failed", 0))
    with m4:
        st.metric("Skipped", last.get("skipped", 0))
    with m5:
        st.metric("Bounced", last.get("bounced", 0))

    last = send_status.get("last_batch")
    if last and last.get("total", 0) > 0:
        total = int(last["total"])
        delivered = int(last.get("delivered", 0))
        label = "Last batch: accepted by server / total"
        if not send_status.get("smtp_configured"):
            label = "Last batch (demo): simulated OK / total"
        st.progress(min(1.0, delivered / total) if total else 0.0)
        st.caption(f"{label} — {delivered}/{total}")
    else:
        st.progress(0.0)
        st.caption("No send batch yet — use Send")

    st.caption(send_status.get("delivery_note", ""))

    with st.expander("Last batch details"):
        if last:
            st.json(last)
        else:
            st.write("No batches yet.")
else:
    st.warning("Could not load send status from API. Is the backend running?")

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("1) Upload Excel")
    excel_file = st.file_uploader("Excel File", type=["xlsx", "xls"], key="excel_file")
    if st.button("Upload Excel", use_container_width=True):
        if not excel_file:
            st.warning("Choose an Excel file first.")
        else:
            try:
                files = {
                    "file": (
                        excel_file.name,
                        excel_file.getvalue(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                }
                response = requests.post(
                    f"{api_base_url()}/api/upload-excel",
                    files=files,
                    timeout=60,
                )
                data = response.json()
                if response.status_code >= 400:
                    raise RuntimeError(data.get("detail", "Upload failed"))
                st.success(
                    f"Uploaded: {data['rows_count']} rows. "
                    f"First name: {data.get('first_name_column') or 'not detected'}. "
                    f"Email: {data.get('email_column') or 'not detected'}."
                )
                if data.get("columns"):
                    st.info(f"Columns: {', '.join(data['columns'])}")
            except Exception as exc:
                st.error(str(exc))

    st.subheader("2) Upload Attachments")
    attachment_files = st.file_uploader(
        "Attachment files",
        accept_multiple_files=True,
        key="attachment_files",
    )
    if st.button("Save Attachments", use_container_width=True):
        if not attachment_files:
            st.warning("Choose one or more attachments.")
        else:
            try:
                files = [
                    ("files", (f.name, f.getvalue(), "application/octet-stream"))
                    for f in attachment_files
                ]
                response = requests.post(
                    f"{api_base_url()}/api/upload-attachments",
                    files=files,
                    timeout=60,
                )
                data = response.json()
                if response.status_code >= 400:
                    raise RuntimeError(data.get("detail", "Upload failed"))
                st.success(f"Saved {len(data.get('attachments', []))} attachment(s).")
            except Exception as exc:
                st.error(str(exc))

with right_col:
    st.subheader("3) Message")
    objective = st.text_input(
        "Campaign Objective",
        placeholder="Invite leads to your product demo",
    )
    subject = st.text_input("Subject", placeholder="Quick follow-up")

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("Generate Message", use_container_width=True):
            if not objective.strip():
                st.warning("Enter campaign objective first.")
            else:
                try:
                    data = post_json("/api/generate-message", {"objective": objective})
                    st.session_state.message = data["message"]
                    st.success("Message generated.")
                except Exception as exc:
                    st.error(str(exc))
    with action_col2:
        if st.button("Enhance by AI", use_container_width=True):
            if not st.session_state.message.strip():
                st.warning("Write or generate message first.")
            else:
                try:
                    data = post_json(
                        "/api/enhance-message",
                        {"message": st.session_state.message},
                    )
                    st.session_state.message = data["message"]
                    st.success("Message enhanced.")
                except Exception as exc:
                    st.error(str(exc))
    with action_col3:
        if st.button("Preview", use_container_width=True):
            if not st.session_state.message.strip():
                st.warning("Message cannot be empty.")
            else:
                try:
                    data = post_json(
                        "/api/preview",
                        {"message_template": st.session_state.message, "limit": 5},
                    )
                    st.session_state.preview = data.get("previews", [])
                    st.success(f"Preview generated for {data.get('count', 0)} rows.")
                except Exception as exc:
                    st.error(str(exc))

    st.session_state.message = st.text_area(
        "Message Textbox",
        value=st.session_state.message,
        height=260,
        placeholder="Hi {first_name}, ...",
    )
    st.caption("Use placeholders from Excel headers, e.g. {first_name}, {company}, {email}.")

    if st.button("Send (Demo)", type="primary", use_container_width=True):
        if not subject.strip() or not st.session_state.message.strip():
            st.warning("Subject and message are required.")
        else:
            try:
                data = post_json(
                    "/api/send",
                    {
                        "subject": subject.strip(),
                        "message_template": st.session_state.message,
                    },
                )
                st.success(
                    f"{data.get('message', 'Sent')}. Recipients: {data.get('total_recipients', 0)}"
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


st.subheader("4) Preview Output")
if not st.session_state.preview:
    st.info("No preview yet. Upload Excel, write message, and click Preview.")
else:
    for idx, item in enumerate(st.session_state.preview, start=1):
        recipient = item.get("recipient", {})
        label = (
            recipient.get("first_name")
            or recipient.get("FirstName")
            or recipient.get("email")
            or f"Recipient {idx}"
        )
        st.markdown(f"**{label}**")
        st.code(item.get("message", ""), language="text")
        with st.expander("Recipient Row Data"):
            st.code(json.dumps(recipient, indent=2), language="json")


#AI Chat 
# st.divider()
# st.subheader("🤖 AI Assistant (Chatbot)")

# chat_container = st.container()

# with chat_container:
#     for msg in st.session_state.chat_history:
#         if msg["role"] == "user":
#             st.markdown(f"**You:** {msg['content']}")
#         else:
#             st.markdown(f"**Bot:** {msg['content']}")

# col1, col2 = st.columns([4, 1])

# with col1:
#     user_input = st.text_input("Type your message...", key="chat_input")

# with col2:
#     send_btn = st.button("Send", use_container_width=True)

# if send_btn and user_input.strip():
#     try:
#         # Save user message
#         st.session_state.chat_history.append({
#             "role": "user",
#             "content": user_input
#         })

#         # Call chatbot API
#         response = requests.get(
#             f"{api_base_url()}/chat",
#             params={"query": user_input},
#             timeout=60
#         )

#         data = response.json()

#         bot_reply = data.get("message", "No response")

#         # Save bot reply
#         st.session_state.chat_history.append({
#             "role": "bot",
#             "content": bot_reply
#         })

#         st.rerun()

#     except Exception as e:
#         st.error(f"Chat error: {e}")