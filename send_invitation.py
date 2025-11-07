from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date, datetime, timezone
from typing import List
import logging

from app.database.database import get_session
from app.models.models import Prueba, Notificacion, Colaborador  # <-- asegúrate de que el nombre sea correcto
from pydantic import BaseModel

# Usa tu mailer existente
from app.mailer import enviar_correo_custom  # o: from app.mailer import enviar_correo

router = APIRouter()
log = logging.getLogger("enviar_invitaciones")

class InvitacionRequest(BaseModel):
    id_lider: int
    colaboradores_ids: List[int]

class ResultadoOK(BaseModel):
    id: int
    email: str
    id_prueba: int

class ResultadoFail(BaseModel):
    id: int
    error: str

class InvitacionResponse(BaseModel):
    total: int
    enviados: List[ResultadoOK]
    fallidos: List[ResultadoFail]


@router.post("/enviar-invitaciones/", response_model=InvitacionResponse)
def enviar_invitaciones(
    solicitud: InvitacionRequest,
    session: Session = Depends(get_session)
):
    colaboradores_ids = solicitud.colaboradores_ids or []
    if not colaboradores_ids:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un colaborador")

    enviados: List[ResultadoOK] = []
    fallidos: List[ResultadoFail] = []

    # Texto de notificación in-app
    notif_texto = "Tu líder te ha enviado una prueba. Realízala ahora"

    for colaborador_id in colaboradores_ids:
        try:
            # 1) Traer colaborador (para validar existencia y obtener email)
            col = session.exec(
                select(Colaborador).where(Colaborador.id == colaborador_id)
            ).first()

            if not col:
                fallidos.append(ResultadoFail(id=colaborador_id, error="Colaborador no encontrado"))
                continue

            if not getattr(col, "email", None):
                fallidos.append(ResultadoFail(id=colaborador_id, error="Colaborador sin email"))
                continue

            # 2) Crear PRUEBA (pendiente)
            nueva_prueba = Prueba(
                fecha_registro=date.today(),
                fecha_resultado=date.today(),   # si quieres, déjalo en None hasta que haya resultado
                id_colaborador=colaborador_id,
                estado=0,        # Pendiente
                resultado=False  # aún sin resultado
            )
            session.add(nueva_prueba)
            session.commit()
            session.refresh(nueva_prueba)

            # 3) Crear NOTIFICACIÓN in-app
            nueva_notificacion = Notificacion(
                id_colaborador=colaborador_id,
                id_prueba=nueva_prueba.id,
                mensaje=notif_texto,
                leido=False
            )
            session.add(nueva_notificacion)
            session.commit()

            # 4) Enviar correo (no tumba el lote si falla)
            try:
                asunto = "Nueva prueba disponible en StressLess"
                cuerpo = (
                    f"Hola,\n\n"
                    f"{notif_texto}.\n"
                    f"ID de la prueba: {nueva_prueba.id}\n\n"
                    f"— StressLess"
                )
                # Usa tu función; si prefieres HTML, cambia enviar_correo_custom a HTML y añade headers en tu mailer
                enviar_correo_custom(destinatario=col.email, asunto=asunto, cuerpo=cuerpo)
                # Alternativa (si prefieres tu otra función):
                # enviar_correo(destinatario=col.email, otp="")  # si quisieras OTP
            except Exception as mail_err:
                # No revertimos la creación de prueba/notification: solo registramos el fallo del correo
                log.exception(f"Fallo al enviar correo a {col.email}: {mail_err}")
                fallidos.append(ResultadoFail(id=colaborador_id, error=f"Email: {str(mail_err)[:300]}"))
                # Aun así lo contamos como creado (prueba y notificación existen), por eso no continuamos

            # 5) Éxito (contando que la prueba existe)
            enviados.append(ResultadoOK(id=colaborador_id, email=col.email, id_prueba=nueva_prueba.id))

        except Exception as e:
            # Si falló crear prueba o notificación, revertimos SOLO esta iteración
            session.rollback()
            log.exception(f"Error con colaborador {colaborador_id}: {e}")
            fallidos.append(ResultadoFail(id=colaborador_id, error=str(e)[:300]))
            # seguimos con el siguiente

    return InvitacionResponse(
        total=len(colaboradores_ids),
        enviados=enviados,
        fallidos=fallidos
    )
