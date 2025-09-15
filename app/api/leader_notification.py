from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database.database import get_session
from app.auth.jwt import verify_token
from app.models.models import NotificacionLider, Colaborador

router = APIRouter()

@router.get("/lider/{id_lider}/notificaciones")
def listar_notificaciones_lider(
    id_lider: int,
    session: Session = Depends(get_session),
    token = Depends(verify_token)
):
    if token.get("rol") != "LIDER" or int(token.get("id")) != id_lider:
        raise HTTPException(status_code=403, detail="No autorizado")

    notis = session.exec(
        select(NotificacionLider)
        .where(NotificacionLider.id_lider == id_lider)
        .order_by(NotificacionLider.creado_en.desc())
    ).all()

    out = []
    for n in notis:
        col = session.get(Colaborador, n.id_colaborador)
        out.append({
            "id": n.id,
            "id_colaborador": n.id_colaborador,
            "colaborador": col.nombre if col else None,
            "consecutivas": n.consecutivas,
            "mensaje": n.mensaje,
            "creado_en": n.creado_en.isoformat(),
            "leido": n.leido,
        })
    return out


@router.put("/lider/notificacion/{id}/leido")
def marcar_leida(
    id: int,
    session: Session = Depends(get_session),
    token = Depends(verify_token)
):
    noti = session.get(NotificacionLider, id)
    if not noti:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if token.get("rol") != "LIDER" or int(token.get("id")) != noti.id_lider:
        raise HTTPException(status_code=403, detail="No autorizado")

    noti.leido = True
    session.add(noti)
    session.commit()
    return {"mensaje": "Notificación marcada como leída"}
