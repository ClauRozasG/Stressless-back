from fastapi import FastAPI
import os
from sqlmodel import create_engine
from app.auth.auth import router as auth_router
from app.api.leader import router as leader_router
from app.api.collaborator import router as collaborator_router
from app.api.invitation import router as invitation_router
from app.database.database import create_tables
from app.api.prueba import router as prueba_router
from app.modelo_ML import router as ml_router
from app.register_colaborator import router as register_colab_router
from app.database.database import create_tables
from app.api.send_invitation import router as notificaciones_router
from app.api.password import router as password_router
##from app.api.schedules import router as schedules_router
from app.api.schedules import router as calendar_router
from app.api.leader_notification import router as leader_notifs_router
from app.scheduler import scheduler_loop
from datetime import datetime
import pytz
import asyncio

app = FastAPI()

app.include_router(auth_router)
app.include_router(leader_router)
app.include_router(collaborator_router)
app.include_router(invitation_router)
app.include_router(prueba_router)
app.include_router(ml_router)
app.include_router(register_colab_router)
app.include_router(notificaciones_router)
app.include_router(leader_notifs_router)
app.include_router(password_router)
app.include_router(calendar_router)

@app.on_event("startup")
def on_startup():
    create_tables()
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_loop(poll_seconds=30))

def utc_to_lima(utc_dt: datetime):
    lima_tz = pytz.timezone("America/Lima")
    return utc_dt.astimezone(lima_tz)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ahora")
def ahora():
    utc_now = datetime.utcnow()
    lima_now = utc_to_lima(utc_now)
    return {
        "utc": utc_now.isoformat(),
        "lima": lima_now.isoformat()
    }
