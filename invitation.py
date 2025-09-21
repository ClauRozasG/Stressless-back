from datetime import date, datetime, timedelta
from typing import List
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from app.auth.jwt import verify_token, verify_token_optional
from app.database.database import get_session
from app.models.models import Colaborador, Invitacion, Lider, LiderColaborador, PreColaborador
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from email_utils import enviar_correo
from datetime import datetime
import random
import string


router = APIRouter()

def generar_otp(longitud=5):
    return ''.join(random.choices(string.digits, k=longitud))


class InvitationRequest(BaseModel):
    id_lider:int
    collaborators:List[int]

@router.post("/invitation")
def createInvitation(request:InvitationRequest,session:Session = Depends(get_session),token = Depends(verify_token)):
    
    if token["id"] != request.id_lider:
        raise HTTPException(status_code=401, detail="Lider no encontrado")
    
    invitacion:Invitacion = Invitacion(fecha_envio=datetime.now(),fecha_respuesta=None,estado=True,codigo=generar_otp())

    session.add(invitacion)
    session.commit()
    session.refresh(invitacion)

    for i in request.collaborators:
        item = LiderColaborador(
            id_lider=request.id_lider,
            id_colaborador=i,
            estado="Pendiente",
            id_invitacion=invitacion.id,
            fecha_inicio=datetime.now(),
            fecha_fin=None
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        consulta = select(Colaborador).where(Colaborador.id == i)
        colaborador = session.exec(consulta).first()

        enviar_correo(colaborador.correo, invitacion.codigo)

    return token

@router.post("/send-invitations/{id_lider}")
def send_invitations(id_lider: int, session: Session = Depends(get_session), token = Depends(verify_token_optional)):
    lider = session.exec(select(Lider).where(Lider.id == id_lider)).first()
    if not lider:
        raise HTTPException(status_code=404, detail="Líder no encontrado")

    precolabs = session.exec(
        select(PreColaborador).where(PreColaborador.correo_lider == lider.correo)
    ).all()

    if not precolabs:
        raise HTTPException(status_code=404, detail="No hay precolaboradores para este líder")

    enviados = []

    if token and token.get("id") != id_lider:
        raise HTTPException(status_code=401, detail="Líder no coincide con token")
    
    for precolab in precolabs:
        # Generar un OTP único por colaborador
        otp = generar_otp()

        # Crear la invitación
        invitacion = Invitacion(
            id_precolaborador=precolab.id,
            fecha_envio=date.today(),
            fecha_respuesta=date.today(),
            estado=False,
            codigo=otp,
        )
        session.add(invitacion)
        session.commit()
        session.refresh(invitacion)

        # Relación en tabla intermedia
        relacion = LiderColaborador(
            id_lider=id_lider,
            id_colaborador=None,
            estado="pendiente",
            id_invitacion=invitacion.id,
            fecha_inicio=date.today(),
            fecha_fin=date.today()
        )
        session.add(relacion)
        session.commit()

        # Enviar el correo con el código único
        enviar_correo(precolab.correo, otp)

        enviados.append({
            "nombre": precolab.nombre,
            "correo": precolab.correo,
            "codigo": otp
        })

    session.commit()
    return {"mensaje": "Invitaciones enviadas", "invitaciones": enviados}

@router.get("/precolaboradores/{correo_lider}")
def obtener_precolaboradores(correo_lider: str, session: Session = Depends(get_session)):
    precolabs = session.exec(
        select(PreColaborador).where(PreColaborador.correo_lider == correo_lider)
    ).all()
    return precolabs


class ResendCodeRequest(BaseModel):
    correo: EmailStr  # correo del colaborador

@router.post("/resend-code")
def resend_code(data: ResendCodeRequest, session: Session = Depends(get_session)):
    """
    Reenvía el OTP de invitación a un precolaborador. Si ya existe una invitación
    no usada (estado=False), reenvía ese código. Si no existe, crea una nueva.
    """
    correo = data.correo.lower()

    # 1) Buscar precolaborador por correo
    precolab = session.exec(
        select(PreColaborador).where(PreColaborador.correo == correo)
    ).first()
    if not precolab:
       
        return {"mensaje": "Si el correo está registrado, se ha reenviado el código."}

    
    invitacion = session.exec(
        select(Invitacion).where(
            Invitacion.id_precolaborador == precolab.id,
            Invitacion.estado == False
        ).order_by(Invitacion.fecha_envio.desc())
    ).first()

    
    if invitacion and (datetime.utcnow().date() == invitacion.fecha_envio):
        
        pass  

    
    if not invitacion:
        codigo = generar_otp(5)
        invitacion = Invitacion(
            id_precolaborador=precolab.id,
            fecha_envio=date.today(),
            fecha_respuesta=date.today(), 
            estado=False,
            codigo=codigo
        )
        session.add(invitacion)
        session.commit()
        session.refresh(invitacion)

        
        lider = session.exec(
            select(Lider).where(Lider.correo == precolab.correo_lider)
        ).first()

        if lider:
            
            ya_rel = session.exec(
                select(LiderColaborador).where(
                    LiderColaborador.id_invitacion == invitacion.id
                )
            ).first()
            if not ya_rel:
                relacion = LiderColaborador(
                    id_lider=lider.id,
                    id_colaborador=None,
                    estado="pendiente",
                    id_invitacion=invitacion.id,
                    fecha_inicio=date.today(),
                    fecha_fin=date.today()
                )
                session.add(relacion)
                session.commit()


    try:
        enviar_correo(precolab.correo, invitacion.codigo)
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo enviar el correo en este momento")

    return {"mensaje": "Si el correo está registrado, se ha reenviado el código."}
