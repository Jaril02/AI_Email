import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL_NAME", "openai/gpt-3.5-turbo")

def enhance_email(text: str):
    try:
        if not API_KEY:
            return text  # fallback

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Improve this email professionally."},
                {"role": "user", "content": text}
            ]
        }

        res = requests.post(url, headers=headers, json=payload, timeout=30)

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            return text

    except Exception:
        return text