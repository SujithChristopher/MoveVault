# core/email_utils.py
import smtplib
from email.mime.text import MIMEText

EMAIL_SMTP_SERVER="smtp.gmail.com"
EMAIL_PORT=465
EMAIL_SENDER="homerstudy2025@gmail.com"
EMAIL_PASSWORD="advy esrw nepp wqdi"
ADMIN_EMAIL="homerstudy2025@gmail.com"

def send_upload_report(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ADMIN_EMAIL

    try:
        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Upload report email sent to admin.")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
