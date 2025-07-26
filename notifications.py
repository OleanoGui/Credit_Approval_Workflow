import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, body, from_email="no-reply@creditworkflow.com"):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP("smtp.seuservidor.com", 587) as server:
        server.starttls()
        server.login("usuario", "senha")
        server.sendmail(from_email, [to_email], msg.as_string())

def send_sms(phone_number, message):
    print(f"SMS to {phone_number}: {message}")

def send_notification(user, subject, message):
    if getattr(user, "notify_email", False) and getattr(user, "email", None):
        send_email(user.email, subject, message)
    if getattr(user, "notify_sms", False) and getattr(user, "phone", None):
        send_sms(user.phone, message)