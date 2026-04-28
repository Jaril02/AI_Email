import json
from typing import Any

import requests
import streamlit as st


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AI Email Automation Agent", layout="wide")
st.title("AI Agent for Email Automation")


# =========================
# SESSION STATE
# =========================
if "message" not in st.session_state:
    st.session_state.message = ""

if "preview" not in st.session_state:
    st.session_state.preview = []

if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False


# =========================
# API HELPERS
# =========================
def api_base_url() -> str:
    return st.session_state.get("api_base_url", "http://127.0.0.1:8000")


def get_json(endpoint: str) -> dict[str, Any] | None:
    try:
        res = requests.get(f"{api_base_url()}{endpoint}", timeout=60)
        if res.status_code >= 400:
            return None
        return res.json()
    except Exception:
        return None


def post_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    res = requests.post(f"{api_base_url()}{endpoint}", json=payload, timeout=60)
    data = res.json()
    if res.status_code >= 400:
        raise RuntimeError(data.get("detail", "Request failed"))
    return data


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("Backend")
    st.session_state.api_base_url = st.text_input(
        "FastAPI URL", value=api_base_url()
    )
    st.caption("Run backend: uvicorn app.main:app --reload")


# =========================
# SEND STATUS
# =========================
send_status = get_json("/api/send-status")

if send_status and send_status.get("success"):
    last = send_status.get("last_batch") or {}

    st.subheader("Send status")
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total", last.get("total", 0))
    c2.metric("Delivered", last.get("delivered", 0))
    c3.metric("Failed", last.get("failed", 0))
    c4.metric("Skipped", last.get("skipped", 0))
    c5.metric("Bounced", last.get("bounced", 0))

    if last.get("total"):
        progress = last.get("delivered", 0) / last.get("total", 1)
        st.progress(progress)

    with st.expander("Last batch details"):
        st.json(last)

else:
    st.warning("Backend not connected.")


st.divider()

left_col, right_col = st.columns(2)

# =========================
# LEFT SIDE
# =========================
with left_col:
    st.subheader("1) Upload Excel")

    file = st.file_uploader("Excel File", type=["xlsx", "xls"])

    if st.button("Upload Excel", use_container_width=True):
        if not file:
            st.warning("Upload file first")
        else:
            try:
                res = requests.post(
                    f"{api_base_url()}/api/upload-excel",
                    files={"file": (file.name, file.getvalue())},
                )
                data = res.json()
                st.success(f"{data['rows_count']} rows uploaded")
            except Exception as e:
                st.error(str(e))

    st.subheader("2) Attachments")

    files = st.file_uploader(
        "Upload attachments",
        accept_multiple_files=True
    )

    if st.button("Save Attachments"):
        if files:
            try:
                req_files = [
                    ("files", (f.name, f.getvalue()))
                    for f in files
                ]
                res = requests.post(
                    f"{api_base_url()}/api/upload-attachments",
                    files=req_files
                )
                st.success("Attachments uploaded")
            except Exception as e:
                st.error(str(e))


# =========================
# RIGHT SIDE
# =========================
with right_col:
    st.subheader("3) Message")

    objective = st.text_input("Campaign Objective")
    subject = st.text_input("Subject")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Generate"):
            data = post_json("/api/generate-message", {"objective": objective})
            st.session_state.message = data["message"]

    with c2:
        if st.button("Enhance"):
            data = post_json(
                "/api/enhance-message",
                {"message": st.session_state.message}
            )
            st.session_state.message = data["message"]

    with c3:
        if st.button("Preview"):
            data = post_json(
                "/api/preview",
                {"message_template": st.session_state.message, "limit": 5}
            )
            st.session_state.preview = data["previews"]

    st.session_state.message = st.text_area(
        "Message",
        value=st.session_state.message,
        height=200
    )

    # =========================
    # SEND MODE
    # =========================
    st.subheader("4) Send Mode")

    mode = st.radio(
        "Mode",
        ["Auto", "Manual"],
        horizontal=True
    )

    st.session_state.manual_mode = mode == "Manual"

    # =========================
    # SEND ACTIONS
    # =========================
    if not st.session_state.manual_mode:
        if st.button("Send Bulk", type="primary"):
            data = post_json(
                "/api/send",
                {
                    "subject": subject,
                    "message_template": st.session_state.message
                }
            )
            st.success(data["message"])
            st.rerun()

    else:
        st.info("Manual Mode Enabled")

        col1, col2, col3, col4 = st.columns(4)

        # Preview
        with col1:
            if st.button("Preview Next"):
                data = get_json("/api/manual/preview")

                if data:
                    st.markdown(f"**To:** {data.get('to')}")
                    st.markdown(f"**Subject:** {data.get('subject')}")
                    st.code(data.get("body", ""))

        # Send
        with col2:
            if st.button("Send Next", type="primary"):
                data = post_json(
                    "/api/manual/send",
                    {
                        "subject": subject,
                        "message_template": st.session_state.message
                    }
                )
                st.success(f"Sent → {data.get('to')}")
                st.rerun()

        # Skip
        with col3:
            if st.button("Skip"):
                data = post_json("/api/manual/skip", {})
                st.warning(data.get("message"))
                st.rerun()

        # Status
        with col4:
            if st.button("Status"):
                data = get_json("/api/manual/status")

                if data:
                    st.metric("Total", data.get("total", 0))
                    st.metric("Sent", data.get("current_index", 0))
                    st.metric("Remaining", data.get("remaining", 0))

                    if data.get("total"):
                        st.progress(
                            data["current_index"] / data["total"]
                        )

        # Reset
        if st.button("Reset Manual Session"):
            post_json("/api/manual/reset", {})
            st.success("Reset done")
            st.rerun()


#emergency controls

st.subheader("🚨 Emergency Control")

col1, col2 = st.columns(2)

with col1:
    if st.button("🛑 STOP ALL EMAILS", use_container_width=True):
        try:
            post_json("/api/stop", {})
            st.error("Emergency stop activated!")
        except Exception as e:
            st.error(str(e))

with col2:
    if st.button("🔄 Reset Stop", use_container_width=True):
        try:
            post_json("/api/stop/reset", {})
            st.success("Stop reset")
        except Exception as e:
            st.error(str(e))


# =========================
# PREVIEW OUTPUT
# =========================
st.subheader("5) Preview Output")

if not st.session_state.preview:
    st.info("No preview yet")
else:
    for i, item in enumerate(st.session_state.preview, 1):
        st.markdown(f"**Recipient {i}**")
        st.code(item.get("message", ""))