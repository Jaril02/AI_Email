import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

def enhance_email(text: str):
    try:
        print (API_KEY)
        if not API_KEY:
            return text

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "AI Email Automation Agent"
        }

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert email copywriter. "
                        "Rewrite the email to be more professional, engaging, and persuasive. "
                        "Keep it concise and clear. Preserve placeholders like {first_name}. in the content"
                        "dont add subject line"
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            "temperature": 0.7
        }

        res = requests.post(url, headers=headers, json=payload, timeout=30)

        print("STATUS:", res.status_code)
       

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            return text

    except Exception as e:
        print("ERROR:", str(e))
        return text
if __name__ == "__main__":
    enhance_email("hello")