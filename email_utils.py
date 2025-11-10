# email.py  – envío por Brevo HTTP API
import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "aledisuma@gmail.com")

def enviar_correo(destinatario: str, otp: str):
    """
    Envía el correo de invitación con el OTP usando la API HTTP de Brevo.
    Gratis y funciona en Render.
    """
    cuerpo_html = f"""
    <p>Hola,</p>
    <p>Has recibido una invitación para unirte a la app de detección de estrés.</p>
    <p>Usa este código OTP para aceptar la invitación: <b>{otp}</b></p>
    <p>— StressLess</p>
    """
    data = {
        "sender": {"email": FROM_EMAIL, "name": "StressLess"},
        "to": [{"email": destinatario}],
        "subject": "Invitación a la app de estrés laboral",
        "htmlContent": cuerpo_html
    }

    r = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
        json=data
    )
    if r.status_code >= 400:
        raise Exception(f"Error enviando correo: {r.status_code}, {r.text}")

def enviar_correo_custom(destinatario: str, asunto: str, cuerpo: str):
    """
    Versión para otros mensajes personalizados.
    """
    data = {
        "sender": {"email": FROM_EMAIL, "name": "StressLess"},
        "to": [{"email": destinatario}],
        "subject": asunto,
        "htmlContent": f"<p>{cuerpo}</p>"
    }

    r = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
        json=data
    )
    if r.status_code >= 400:
        raise Exception(f"Error enviando correo: {r.status_code}, {r.text}")
