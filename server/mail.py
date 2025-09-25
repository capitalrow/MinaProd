import smtplib, ssl
from email.message import EmailMessage
from flask import current_app

def send_mail(to_email: str, subject: str, body_text: str):
    host = current_app.config["SMTP_HOST"]
    port = current_app.config["SMTP_PORT"]
    user = current_app.config["SMTP_USERNAME"]
    pwd  = current_app.config["SMTP_PASSWORD"]
    use_tls = current_app.config["SMTP_USE_TLS"]
    sender = current_app.config["MAIL_FROM"]

    if not host or not user or not pwd:
        raise RuntimeError("SMTP not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(body_text)

    if use_tls:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port) as s:
            s.starttls(context=ctx)
            s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.login(user, pwd)
            s.send_message(msg)