from typing import Any, Dict, List, Optional
from app.email_service import SMTPSettings, send_email_smtp


class ManualEmailSender:
    def __init__(self, emails: List[Dict], settings: SMTPSettings | None,state):
        self.emails = emails
        self.settings = settings
        self.state = state
        self.index = 0

    def preview_next(self) -> Optional[Dict]:
        if self.index >= len(self.emails):
            return None
        return self.emails[self.index]

    def send_next(self) -> Dict:

        if self.state.get("stop_requested"):
            return {"message": "🛑 Sending stopped"}
        if self.index >= len(self.emails):
            return {"message": "All emails sent"}
        


        email = self.emails[self.index]

        try:
            if self.settings:
                send_email_smtp(
                    to_addr=email["to"],
                    subject=email["subject"],
                    body=email["body"],
                    settings=self.settings,
                    attachments=email.get("attachments", []),
                )

            result = {
                "to": email["to"],
                "status": "sent",
                "index": self.index
            }

            self.index += 1
            return result

        except Exception as e:
            return {"to": email["to"], "status": "failed", "error": str(e)}

    def skip_next(self):
        if self.index < len(self.emails):
            skipped = self.emails[self.index]["to"]
            self.index += 1
            return {"message": f"Skipped {skipped}"}

        return {"message": "Nothing to skip"}

    def status(self):
        return {
            "total": len(self.emails),
            "current_index": self.index,
            "remaining": len(self.emails) - self.index,
        }

    def has_more(self) -> bool:
        return self.index < len(self.emails)