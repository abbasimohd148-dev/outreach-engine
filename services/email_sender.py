import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:

    def __init__(self):
        # 🔐 Use your Gmail + App Password (NOT normal password)
        self.email = "abbasimohd298@gmail.com"
        self.password = "jkcxvqjsxgtnfpqs"

    def send_email(self, to_email, subject, body):
        try:
            # ✅ Create message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            # ✅ Connect to Gmail SMTP
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()

            # ✅ Login
            server.login(self.email, self.password)

            # ✅ Send email
            server.sendmail(self.email, to_email, msg.as_string())

            server.quit()

            print(f"✅ Email sent to {to_email}")

        except Exception as e:
            print(f"❌ SEND ERROR to {to_email}: {e}")