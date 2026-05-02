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


def api_base_url() -> str:
    return st.session_state.get("api_base_url", "http://127.0.0.1:8000")


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
                    f"First-name column: {data.get('first_name_column') or 'not detected'}"
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