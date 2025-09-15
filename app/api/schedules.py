from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.database.database import get_session
from app.auth.jwt import verify_token
from app.models.models import AgendaPrueba

router = APIRouter()


class FechaHora(BaseModel):
    fecha: date               # YYYY-MM-DD
    hora: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "HH:MM"  # "HH:MM"

class CalendarQueueRequest(BaseModel):
    timezone: str = "America/Lima"
    colaboradores_ids: List[int]
    slots: List[FechaHora]    


def to_utc(dt_local: datetime, tzname: str) -> datetime:
    
    return dt_local.replace(tzinfo=ZoneInfo(tzname)).astimezone(ZoneInfo("UTC"))


@router.post("/calendar/queue")
def calendar_queue(
    data: CalendarQueueRequest,
    session: Session = Depends(get_session),
    token = Depends(verify_token)
):
    
    if token.get("rol") != "LIDER":
        raise HTTPException(status_code=403, detail="No autorizado")
    leader_id = int(token.get("id"))

    
    hoy = date.today()
    limite = hoy + timedelta(days=7)

    to_insert: List[AgendaPrueba] = []
    for slot in data.slots:
        if not (hoy <= slot.fecha <= limite):
            raise HTTPException(status_code=400, detail="Solo se puede programar dentro de los próximos 7 días")

        hh, mm = map(int, slot.hora.split(":"))
        dt_local = datetime(slot.fecha.year, slot.fecha.month, slot.fecha.day, hh, mm, 0)
        dt_utc = to_utc(dt_local, data.timezone)

        for cid in data.colaboradores_ids:
            to_insert.append(AgendaPrueba(
                id_lider=leader_id,
                id_colaborador=cid,
                scheduled_at=dt_utc,
                estado=0
            ))

    
    for item in to_insert:
        session.add(item)
    session.commit()

    return {"mensaje": f"{len(to_insert)} envíos programados"}

@router.get("/calendar/upcoming")
def calendar_upcoming(
    tz: str = "America/Lima",
    session: Session = Depends(get_session),
    token = Depends(verify_token)
):
    if token.get("rol") != "LIDER":
        raise HTTPException(status_code=403, detail="No autorizado")
    leader_id = int(token.get("id"))

    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    semana_utc = now_utc + timedelta(days=7)

    items = session.exec(
        select(AgendaPrueba)
        .where(
            AgendaPrueba.id_lider == leader_id,
            AgendaPrueba.estado == 0,
            AgendaPrueba.scheduled_at.between(now_utc, semana_utc)
        )
        .order_by(AgendaPrueba.scheduled_at.asc())
    ).all()

    
    out = []
    tzinfo = ZoneInfo(tz)
    for it in items:
        
        scheduled_local = it.scheduled_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tzinfo)
        out.append({
            "id": it.id,
            "id_lider": it.id_lider,
            "id_colaborador": it.id_colaborador,
            "estado": it.estado,
            "scheduled_at_utc": it.scheduled_at,     # para depurar
            "scheduled_at_local": scheduled_local,   # para mostrar
        })
    return out


@router.delete("/calendar/{agenda_id}")
def calendar_cancel(
    agenda_id: int,
    session: Session = Depends(get_session),
    token = Depends(verify_token)
):
    if token.get("rol") != "LIDER":
        raise HTTPException(status_code=403, detail="No autorizado")
    leader_id = int(token.get("id"))

    item = session.get(AgendaPrueba, agenda_id)
    if not item or item.id_lider != leader_id:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    if item.estado != 0:
        raise HTTPException(status_code=400, detail="No se puede cancelar: ya fue despachado o cancelado")

    item.estado = 2
    session.add(item)
    session.commit()
    return {"mensaje": "Programación cancelada"}
