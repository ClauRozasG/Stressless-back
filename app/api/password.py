from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from datetime import datetime, timedelta
import random, string, bcrypt

from app.database.database import get_session
from app.models.models import ResetContrasena, Lider, Colaborador
from email_utils import enviar_correo_custom

router = APIRouter()


class ForgotRequest(BaseModel):
    correo: EmailStr
    rol: str  

class VerifyRequest(BaseModel):
    correo: EmailStr
    rol: str
    codigo: str  # 6 dígitos

class ResetRequest(BaseModel):
    correo: EmailStr
    rol: str
    codigo: str
    nueva_contrasena: str


def generar_otp(n=6):
    return ''.join(random.choices(string.digits, k=n))

def buscar_usuario(session: Session, rol: str, correo: str):
    if rol.upper() == "LIDER":
        return session.exec(select(Lider).where(Lider.correo == correo)).first()
    if rol.upper() == "COLABORADOR":
        return session.exec(select(Colaborador).where(Colaborador.correo == correo)).first()
    return None


@router.post("/password/forgot")
def password_forgot(data: ForgotRequest, session: Session = Depends(get_session)):
    correo = data.correo.lower()
    rol = data.rol.upper()
    user = buscar_usuario(session, rol, correo)
    
    if user:
        
        anteriores = session.exec(
            select(ResetContrasena).where(
                ResetContrasena.correo == correo,
                ResetContrasena.rol == rol,
                ResetContrasena.usado == False
            )
        ).all()
        for r in anteriores:
            r.usado = True
            session.add(r)

        codigo = generar_otp(6)
        reset = ResetContrasena(
            correo=correo,
            rol=rol,
            codigo=codigo,
            expira_en=datetime.utcnow() + timedelta(minutes=15),
            usado=False
        )
        session.add(reset)
        session.commit()

        # enviar correo
        asunto = "Recuperación de contraseña"
        cuerpo = (
            f"Hola,\n\n"
            f"Tu código de recuperación es: {codigo}\n"
            f"Vence en 15 minutos.\n\n"
            f"Si no solicitaste esto, ignora este mensaje."
        )
        enviar_correo_custom(correo, asunto, cuerpo)

    return {"mensaje": "Si el correo existe, se envió un código de verificación."}

@router.post("/password/verify")
def password_verify(data: VerifyRequest, session: Session = Depends(get_session)):
    correo = data.correo.lower()
    rol = data.rol.upper()
    rec = session.exec(
        select(ResetContrasena).where(
            ResetContrasena.correo == correo,
            ResetContrasena.rol == rol,
            ResetContrasena.codigo == data.codigo,
            ResetContrasena.usado == False
        ).order_by(ResetContrasena.creado_en.desc())
    ).first()

    if not rec or rec.expira_en < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código inválido o expirado")

    return {"valido": True}

@router.post("/password/reset")
def password_reset(data: ResetRequest, session: Session = Depends(get_session)):
    correo = data.correo.lower()
    rol = data.rol.upper()
    rec = session.exec(
        select(ResetContrasena).where(
            ResetContrasena.correo == correo,
            ResetContrasena.rol == rol,
            ResetContrasena.codigo == data.codigo,
            ResetContrasena.usado == False
        ).order_by(ResetContrasena.creado_en.desc())
    ).first()

    if not rec or rec.expira_en < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código inválido o expirado")

    user = buscar_usuario(session, rol, correo)
    if not user:
        
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # actualizar password
    hashed = bcrypt.hashpw(data.nueva_contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user.contrasenia = hashed
    session.add(user)

    # invalidar el código
    rec.usado = True
    session.add(rec)

    session.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}
