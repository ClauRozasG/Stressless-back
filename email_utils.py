import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def enviar_correo(destinatario: str, otp: str):
    cuerpo = f"""
    Hola, has recibido una invitación para unirte a la app de detección de estrés.
    Usa este código OTP para aceptar la invitación: {otp}
    """

    mensaje = MIMEText(cuerpo)
    mensaje["Subject"] = "Invitación a la app de estrés laboral"
    mensaje["From"] = EMAIL_USER
    mensaje["To"] = destinatario

    print("EMAIL_USER", EMAIL_USER)
    print("EMAIL_PASSWORD",EMAIL_PASSWORD)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(EMAIL_USER, EMAIL_PASSWORD)
        servidor.sendmail(EMAIL_USER, destinatario, mensaje.as_string())

def enviar_correo_custom(destinatario: str, asunto: str, cuerpo: str):
    mensaje = MIMEText(cuerpo)
    mensaje["Subject"] = asunto
    mensaje["From"] = EMAIL_USER
    mensaje["To"] = destinatario

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(EMAIL_USER, EMAIL_PASSWORD)
        servidor.sendmail(EMAIL_USER, destinatario, mensaje.as_string())
