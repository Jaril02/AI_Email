# import os
# import httpx


# class AIClient:
#     def __init__(self) -> None:
#         self.api_key = os.getenv("OPENROUTER_API_KEY")
#         self.base_url = "https://openrouter.ai/api/v1"
#         self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

#     @property
#     def enabled(self) -> bool:
#         return bool(self.api_key)

#     async def generate(self, prompt: str, max_tokens: int = 400) -> str:
#         if not self.enabled:
#             return self._fallback(prompt)

#         url = f"{self.base_url}/chat/completions"

#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json",
#             # Recommended by OpenRouter (important for ranking + stability)
#             "HTTP-Referer": "http://localhost",
#             "X-Title": "AI Email Automation Agent",
#         }

#         payload = {
#             "model": self.model,
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an email writing assistant. "
#                         "Write concise, professional, friendly outreach messages with clear CTA."
#                     ),
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             "temperature": 0.7,
#             "max_tokens": max_tokens,
#         }

#         async with httpx.AsyncClient(timeout=40.0) as client:
#             response = await client.post(url, headers=headers, json=payload)
#             response.raise_for_status()
#             data = response.json()

#             return data["choices"][0]["message"]["content"].strip()

#     def _fallback(self, prompt: str) -> str:
#         return (
#             "Hi {first_name},\n\n"
#             "I hope you are doing well. I wanted to quickly reach out regarding this update:\n"
#             f"{prompt[:500]}\n\n"
#             "If you are available, I would be happy to discuss this in more detail.\n\n"
#             "Best regards,\nYour Name"
#         )


import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

def enhance_email(text: str):
    try:
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