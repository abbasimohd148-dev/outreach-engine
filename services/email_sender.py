import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")

        # 🔥 Validate env variables
        if not self.email or not self.password:
            raise Exception("EMAIL_USER or EMAIL_PASS not set in environment variables")

    def send_email(self, to_email, subject, body):
        try:
            # ✅ Create multipart email (plain + html)
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject

            # ✅ Plain text fallback (important for deliverability)
            plain_text = body.replace("<br>", "\n").replace("<br/>", "\n")

            # ✅ Attach plain version
            part1 = MIMEText(plain_text, "plain")

            # ✅ Attach HTML version (THIS FIXES TRACKING)
            part2 = MIMEText(body, "html")

            msg.attach(part1)
            msg.attach(part2)

            # 🔥 Connect to SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)

            # 🚀 Send email
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent to {to_email}")

        except Exception as e:
            print(f"❌ Email failed to {to_email}: {str(e)}")
            raise e