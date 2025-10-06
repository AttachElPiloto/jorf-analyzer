SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "not commiting this"
EMAIL_TO = "not commiting this"
EMAIL_SUBJECT = "Compte rendu JORF"
EMAIL_PASSWORD = "not commiting this"

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, body_html, from_email=EMAIL_FROM, to_email=EMAIL_TO, smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT, password=EMAIL_PASSWORD):
    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Partie HTML
    part_html = MIMEText(body_html, "html")
    msg.attach(part_html)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("📧 Email envoyé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")