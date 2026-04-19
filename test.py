from app.email_service import load_smtp_settings, send_email_smtp
from validate import validate_email  # adjust import

TEST_EMAILS = [
    "test@gmail.com",
    "navneet@jobjockey",
    "jariljohnson136@gmail.com",
    "user@outlook.com"
]

def run_test():
    settings = load_smtp_settings()

    for email in TEST_EMAILS:
        print("\n-----------------------------")
        print(f"Testing: {email}")

        result = validate_email(email)
        print("Validation Result:", result)

        if result["valid"] and settings:
            print("✅ Valid email → sending test mail...")
            try:
                send_email_smtp(
                    to_addr=email,
                    subject="Test Email",
                    body="This is a test email from your AI agent 🚀",
                    settings=settings
                )
            except Exception as e:
                print("❌ Send failed:", e)
        else:
            print("⚠️ Skipping send (invalid or no SMTP config)")


if __name__ == "__main__":
    run_test()
