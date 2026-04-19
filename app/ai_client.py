import os
import httpx


class AIClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, max_tokens: int = 400) -> str:
        if not self.enabled:
            return self._fallback(prompt)

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Recommended by OpenRouter (important for ranking + stability)
            "HTTP-Referer": "http://localhost",
            "X-Title": "AI Email Automation Agent",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an email writing assistant. "
                        "Write concise, professional, friendly outreach messages with clear CTA."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"].strip()

    def _fallback(self, prompt: str) -> str:
        return (
            "Hi {first_name},\n\n"
            "I hope you are doing well. I wanted to quickly reach out regarding this update:\n"
            f"{prompt[:500]}\n\n"
            "If you are available, I would be happy to discuss this in more detail.\n\n"
            "Best regards,\nYour Name"
        )