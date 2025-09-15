import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.database.database import engine
from app.models.models import AgendaPrueba, Prueba, Notificacion


DEFAULT_TZ = "America/Lima"

async def scheduler_loop(poll_seconds: int = 30):
    while True:
        try:
            
            now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
            
            now_local = now_utc.astimezone(ZoneInfo(DEFAULT_TZ))

            with Session(engine) as session:
                pendientes = session.exec(
                    select(AgendaPrueba)
                    .where(AgendaPrueba.estado == 0, AgendaPrueba.scheduled_at <= now_utc)
                ).all()

                for item in pendientes:
                    
                    prueba = Prueba(
                        
                        fecha_registro=now_local.date(),
                        fecha_resultado=None,
                        id_colaborador=item.id_colaborador,
                        estado=0,          
                        resultado=None
                    )
                    session.add(prueba)
                    session.flush()  

                    noti = Notificacion(
                        id_colaborador=item.id_colaborador,
                        id_prueba=prueba.id,
                        mensaje="Tienes una nueva prueba pendiente",
                        leido=False
                    )
                    session.add(noti)

                    
                    item.estado = 1
                    item.processed_at = now_utc
                    session.add(item)

                session.commit()
        except Exception as e:
            print("[Scheduler] Error:", e)

        await asyncio.sleep(poll_seconds)
