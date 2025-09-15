from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date
from app.database.database import get_session
from app.models.models import Prueba, Notificacion
from pydantic import BaseModel
from typing import List

router = APIRouter()

class InvitacionRequest(BaseModel):
    id_lider: int
    colaboradores_ids: List[int]


@router.post("/enviar-invitaciones/")
def enviar_invitaciones(
    solicitud: InvitacionRequest,
    session: Session = Depends(get_session)
):
    try:
        for colaborador_id in solicitud.colaboradores_ids:
            nueva_prueba = Prueba(
                fecha_registro=date.today(),
                fecha_resultado=date.today(),
                id_colaborador=colaborador_id,
                estado=0,  # Pendiente
                resultado=False
            )
            session.add(nueva_prueba)
            session.commit()
            session.refresh(nueva_prueba)

            nueva_notificacion = Notificacion(
                id_colaborador=colaborador_id,
                id_prueba=nueva_prueba.id,
                mensaje="Tu líder te ha enviado una prueba. Realízala ahora",
                leido=False
            )
            session.add(nueva_notificacion)

        session.commit()
        return {"mensaje": "Invitaciones enviadas correctamente"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al enviar invitaciones: {str(e)}")



@router.put("/notificacion/{id}/leido")
def marcar_notificacion_leida(id: int, session: Session = Depends(get_session)):
    notificacion = session.get(Notificacion, id)
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notificacion.leido = True
    session.add(notificacion)
    session.commit()
    return {"mensaje": "Notificación marcada como leída"}
