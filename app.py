import json
from typing import Any
import requests
import streamlit as st
import re

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AI Email Automation Agent", layout="wide")

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

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
    return "http://127.0.0.1:8000"

def get_json(endpoint: str):
    try:
        res = requests.get(f"{api_base_url()}{endpoint}", timeout=60)
        return res.json()
    except:
        return None

def post_json(endpoint: str, payload: dict[str, Any]):
    try:
        res = requests.post(f"{api_base_url()}{endpoint}", json=payload, timeout=60)
        data = res.json()
        if res.status_code >= 400:
            raise RuntimeError(data.get("detail", "Request failed"))
        return data
    except Exception as e:
        raise RuntimeError(str(e))

# =========================
# AUTH UI
# =========================
def auth_ui():
    st.title("🔐 AI Email Automation System")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # -------- LOGIN --------
    with tab1:
        st.subheader("Login")

        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if not email or not password:
                st.error("Enter email and password")
            else:
                try:
                    res = post_json("/api/login", {
                        "email": email,
                        "password": password
                    })

                    st.session_state.logged_in = True
                    st.session_state.user_role = res["role"]
                    st.session_state.user_id = res["user_id"]

                    st.success("Login successful")
                    st.rerun()

                except Exception as e:
                    st.error(str(e))

    # -------- REGISTER --------
    with tab2:
        st.subheader("Create Account")

        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        password = st.text_input("Password", type="password")

        role = st.selectbox(
            "Account Type",
            ["individual", "organizational"]
        )

        if st.button("Register"):
            if len(name.strip()) < 3:
                st.error("Name must be at least 3 characters")

            elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
                st.error("Enter valid email")

            elif not phone.isdigit() or len(phone) != 10:
                st.error("Phone must be 10 digits")

            elif len(password) < 6:
                st.error("Password must be at least 6 characters")

            else:
                try:
                    res = post_json("/api/register", {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "password": password,
                        "role": role
                    })

                    st.success(res["message"])

                except Exception as e:
                    st.error(str(e))

def organizational_dashboard():
    def organizational_dashboard():
        st.title("🏢 Organizational Panel")

    # =========================
    # SIDEBAR
    # =========================
    with st.sidebar:
        st.header("📂 Navigation")

        page = st.radio(
            "Go to",
            ["📊 Dashboard", "🤖 AI Agent"]
        )

        st.divider()

        try:
            res = requests.get(f"{api_base_url()}/api/senders/{st.session_state.user_id}")
            senders = res.json().get("senders", [])
        except:
            senders = []

        st.subheader("📧 Senders")

        for sender in senders:
            if st.button(sender["email"], key=f"sender_{sender['id']}"):
                requests.post(
                    f"{api_base_url()}/api/senders/select",
                    json={"sender_id": sender["id"]}
                )
                st.session_state.active_email = sender["email"]

    # =========================
    # ACTIVE SENDER
    # =========================
    if "active_email" in st.session_state:
        st.success(f"Active Sender: {st.session_state.active_email}")
    else:
        st.warning("⚠️ Select a sender first")

    st.divider()

    # =========================
    # DASHBOARD PAGE
    # =========================
    if page == "📊 Dashboard":
    
        col1, col2 = st.columns([6, 1])

        with col1:
            st.subheader("📊 Organizational Dashboard")

        with col2:
            if st.button("➕ Add Email"):
                st.session_state.show_form = True

        st.divider()
        if st.session_state.get("show_form"):
            st.write("Form will appear here")  # replace with your form
        # ===== ACTIVE SENDER =====
        if "active_email" in st.session_state:
            st.success(f"Active Sender: {st.session_state.active_email}")
        else:
            st.warning("No sender selected")

        st.divider()

        # ===== ADD EMAIL FORM =====
        if st.session_state.get("show_form"):

            with st.container():
                st.markdown("### ➕ Add New Sender")

                c1, c2 = st.columns(2)

                with c1:
                    name = st.text_input("👤 Name")
                    org = st.text_input("🏢 Organization")

                with c2:
                    email = st.text_input("📧 Email")
                    password = st.text_input("🔑 App Password", type="password")

                st.markdown("[🔗 Generate App Password](https://myaccount.google.com/apppasswords)")

                colA, colB = st.columns(2)

                with colA:
                    if st.button("Save Sender"):
                        res = requests.post(
                            f"{api_base_url()}/api/senders/add",
                            json={
                                "user_id": st.session_state.user_id,
                                "name": name,
                                "organization_name": org,
                                "email": email,
                                "password": password
                            }
                        )

                        if res.status_code == 200:
                            st.success("Sender Added")
                            st.session_state.show_form = False
                            st.rerun()

                with colB:
                    if st.button("Cancel"):
                        st.session_state.show_form = False
                        st.rerun()

            st.divider()

        # ===== SENDER LIST (RIGHT SIDE STYLE) =====
        st.subheader("📬 Sender List")

        if not senders:
            st.info("No senders added yet")
        else:
            for sender in senders:
                with st.container():
                    c1, c2 = st.columns([4,1])

                    with c1:
                        st.markdown(f"""
                        **📧 {sender['email']}**  
                        👤 {sender.get('name','-')}  
                        🏢 {sender.get('organization_name','-')}
                        """)

                    with c2:
                        if st.button("Select", key=f"sel_{sender['id']}"):
                            requests.post(
                                f"{api_base_url()}/api/senders/select",
                                json={"sender_id": sender["id"]}
                            )
                            st.session_state.active_email = sender["email"]
                            st.rerun()

                    st.divider()

    # =========================
    # AI AGENT PAGE
    # =========================
    elif page == "🤖 AI Agent":
        
    # ✅ MUST be inside this block
        if "active_email" not in st.session_state:
            st.error("⚠️ Please select sender first")
            st.stop()

        st.subheader("🤖 AI Email Agent")

        left_col, right_col = st.columns(2)

        # =========================
        # LEFT SIDE
        # =========================
        with left_col:
            st.subheader("1) Upload Excel")

            file = st.file_uploader("Excel File", type=["xlsx", "xls"])

            if st.button("Upload Excel"):
                if file:
                    requests.post(
                        f"{api_base_url()}/api/upload-excel",
                        files={"file": (file.name, file.getvalue())},
                    )
                    st.success("Uploaded")
                else:
                    st.warning("Upload file first")

            st.subheader("2) Attachments")

            files = st.file_uploader("Upload attachments", accept_multiple_files=True)

            if st.button("Save Attachments"):
                if files:
                    req_files = [("files", (f.name, f.getvalue())) for f in files]
                    requests.post(
                        f"{api_base_url()}/api/upload-attachments",
                        files=req_files
                    )
                    st.success("Uploaded")

        # =========================
        # RIGHT SIDE
        # =========================
        with right_col:
            st.subheader("3) Message")

            objective = st.text_input("Campaign Objective")
            subject = st.text_input("Subject")

            c1, c2, c3 = st.columns(3)

            if c1.button("Generate"):
                res = post_json("/api/generate-message", {"objective": objective})
                st.session_state.message = res["message"]

            if c2.button("Enhance"):
                res = post_json("/api/enhance-message", {
                    "message": st.session_state.message
                })
                st.session_state.message = res["message"]

            if c3.button("Preview"):
                res = post_json("/api/preview", {
                    "message_template": st.session_state.message,
                    "limit": 5
                })
                st.session_state.preview = res["previews"]

            st.session_state.message = st.text_area(
                "Message",
                value=st.session_state.message,
                height=200
            )

            if st.button("Send Bulk"):
                res = post_json("/api/send", {
                    "subject": subject,
                    "message_template": st.session_state.message
                })
                st.success(res["message"])

            # =========================
            # PREVIEW OUTPUT
            # =========================
            st.subheader("Preview Output")

            if not st.session_state.preview:
                st.info("No preview yet")
            else:
                for i, item in enumerate(st.session_state.preview, 1):
                    st.markdown(f"**Recipient {i}**")
                    st.code(item.get("message", ""))
# =========================
# LOGIN CHECK
# =========================
if not st.session_state.logged_in:
    auth_ui()
    st.stop()

# 🔥 ROLE-BASED DASHBOARD
if st.session_state.user_role == "organizational":
    organizational_dashboard()
    st.stop()

# =========================
# MAIN APP (UNCHANGED)
# =========================
st.title("📧 AI Agent for Email Automation")

# Logout
if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.rerun()

st.divider()

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

    files = st.file_uploader("Upload attachments", accept_multiple_files=True)

    if st.button("Save Attachments"):
        if files:
            try:
                req_files = [("files", (f.name, f.getvalue())) for f in files]
                requests.post(f"{api_base_url()}/api/upload-attachments", files=req_files)
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
            data = post_json("/api/enhance-message", {
                "message": st.session_state.message
            })
            st.session_state.message = data["message"]

    with c3:
        if st.button("Preview"):
            data = post_json("/api/preview", {
                "message_template": st.session_state.message,
                "limit": 5
            })
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

    mode = st.radio("Mode", ["Auto", "Manual"], horizontal=True)
    st.session_state.manual_mode = mode == "Manual"

    if not st.session_state.manual_mode:
        if st.button("Send Bulk", type="primary"):
            data = post_json("/api/send", {
                "subject": subject,
                "message_template": st.session_state.message
            })
            st.success(data["message"])
            st.rerun()

    else:
        st.info("Manual Mode Enabled")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Preview Next"):
                data = get_json("/api/manual/preview")
                if data:
                    st.markdown(f"**To:** {data.get('to')}")
                    st.markdown(f"**Subject:** {data.get('subject')}")
                    st.code(data.get("body", ""))

        with col2:
            if st.button("Send Next", type="primary"):
                data = post_json("/api/manual/send", {
                    "subject": subject,
                    "message_template": st.session_state.message
                })
                st.success(f"Sent → {data.get('to')}")
                st.rerun()

        with col3:
            if st.button("Skip"):
                data = post_json("/api/manual/skip", {})
                st.warning(data.get("message"))
                st.rerun()

        with col4:
            if st.button("Status"):
                data = get_json("/api/manual/status")
                if data:
                    st.metric("Total", data.get("total", 0))
                    st.metric("Sent", data.get("current_index", 0))
                    st.metric("Remaining", data.get("remaining", 0))
                    if data.get("total"):
                        st.progress(data["current_index"] / data["total"])

        if st.button("Reset Manual Session"):
            post_json("/api/manual/reset", {})
            st.success("Reset done")
            st.rerun()

# =========================
# EMERGENCY CONTROLS
# =========================
st.subheader("🚨 Emergency Control")

col1, col2 = st.columns(2)

with col1:
    if st.button("🛑 STOP ALL EMAILS", use_container_width=True):
        post_json("/api/stop", {})
        st.error("Emergency stop activated!")

with col2:
    if st.button("🔄 Reset Stop", use_container_width=True):
        post_json("/api/stop/reset", {})
        st.success("Stop reset")

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

