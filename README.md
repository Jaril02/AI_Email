# AI Email Automation Agent (FastAPI + Streamlit)

Simple app for:
- Uploading an Excel file of recipients
- Writing or generating an email template with AI
- Enhancing the message by AI
- Previewing personalized messages (`{first_name}` and other column placeholders)
- Preparing for send flow (demo endpoint included)

## 1) Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Configure AI

Copy `.env.example` to `.env` and set your key:

```bash
set OPENAI_API_KEY=your_api_key_here
set OPENAI_MODEL=gpt-4o-mini
```

If no API key is set, the app uses a local fallback template generator.

## 3) Run Backend (FastAPI)

```bash
uvicorn app.main:app --reload
```

## 4) Run Frontend (Streamlit)

```bash
streamlit run streamlit_app.py
```

Open: `http://localhost:8501`

In Streamlit sidebar, keep backend URL as:
`http://127.0.0.1:8000`

## Excel Notes

- Include columns like `first_name`, `email`, `company` etc.
- In your message, use placeholders:
  - `{first_name}` (special handling)
  - Any other `{column_name}` matching Excel header

## Send Endpoint

`/api/send` is currently demo mode and does not deliver real email yet.
Integrate SMTP (e.g., Gmail/Outlook + `smtplib`) or an email service provider API next.
