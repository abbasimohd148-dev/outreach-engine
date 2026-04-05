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

        print("📧 EMAIL_USER:", self.email)
        print("🔑 EMAIL_PASS exists:", bool(self.password))

    def send_email(self, to_email, subject, body):
        try:
            if not self.email or not self.password:
                raise Exception("❌ EMAIL_USER or EMAIL_PASS missing")

            msg = MIMEMultipart("alternative")
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject

            plain_text = body.replace("<br>", "\n").replace("<br/>", "\n")

            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(body, "html")

            msg.attach(part1)
            msg.attach(part2)

            print("🚀 Connecting to SMTP...")

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()

            print("🔐 Logging in...")
            server.login(self.email, self.password)

            print("📤 Sending email...")
            server.send_message(msg)

            server.quit()

            print(f"✅ Email sent to {to_email}")

        except Exception as e:
            print(f"❌ Email failed: {str(e)}")
            raise e