import requests
import os


class EmailSender:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")

    def send_email(self, to_email, subject, body):
        try:
            if not self.api_key:
                raise Exception("❌ RESEND_API_KEY missing")

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "onboarding@resend.dev",  # default working sender
                    "to": [to_email],
                    "subject": subject,
                    "html": body
                }
            )

            print("📨 RESEND RESPONSE:", response.text)

            if response.status_code != 200:
                raise Exception(f"Email failed: {response.text}")

            return True

        except Exception as e:
            print("❌ EMAIL ERROR:", str(e))
            return False