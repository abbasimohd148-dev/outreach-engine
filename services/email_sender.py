import requests
import os


class EmailSender:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")

        print("🔑 RESEND KEY exists:", bool(self.api_key))

        if not self.api_key:
            raise Exception("❌ RESEND_API_KEY missing")

    def send_email(self, to_email, subject, html):
        try:
            url = "https://api.resend.com/emails"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "from": "onboarding@resend.dev",  # test sender
                "to": [to_email],
                "subject": subject or "Quick question",
                "html": html or "<p>Hello</p>"
            }

            print(f"📤 Sending email to {to_email} via Resend...")

            response = requests.post(url, headers=headers, json=payload)

            print("📨 RESEND RESPONSE:", response.status_code, response.text)

            if response.status_code not in [200, 201]:
                raise Exception(f"Email failed: {response.text}")

            print(f"✅ Email sent to {to_email}")

        except Exception as e:
            print(f"❌ Email failed for {to_email}: {str(e)}")
            raise e