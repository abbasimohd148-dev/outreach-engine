import os
import resend


class EmailSender:

    def __init__(self):
        # ✅ Load API key from environment (Render)
        resend.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL")

        if not resend.api_key or not self.from_email:
            raise Exception("❌ RESEND_API_KEY or FROM_EMAIL not set in environment variables")

    def send_email(self, to_email, subject, body):
        try:
            response = resend.Emails.send({
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": f"""
                    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                        <p>{body}</p>
                    </div>
                """
            })

            print(f"✅ Email sent to {to_email}")
            print("📨 Response:", response)

        except Exception as e:
            print(f"❌ SEND ERROR to {to_email}: {str(e)}")
            raise e