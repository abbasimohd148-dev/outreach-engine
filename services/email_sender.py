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

    def send_email(self, to_email, subject, body):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)

            server.send_message(msg)
            server.quit()

            print("✅ Email sent to", to_email)

        except Exception as e:
            print("❌ Email failed:", str(e))
            raise e