import requests
import os


class EmailSender:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")

    def send_email(self, to_email, subject, html):
        try:
            if not self.api_key:
                print("❌ Missing RESEND_API_KEY")
                return False

            url = "https://api.resend.com/emails"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "html": html
            }

            response = requests.post(url, headers=headers, json=payload)

            print("📨 RESEND:", response.status_code, response.text)

            return response.status_code in [200, 201]

        except Exception as e:
            print("❌ EMAIL ERROR:", str(e))
            return False