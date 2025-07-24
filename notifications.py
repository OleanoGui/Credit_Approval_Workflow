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