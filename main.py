from fastapi import FastAPI
from app.auth.auth import router as auth_router
from app.api.leader import router as leader_router
from app.api.collaborator import router as collaborator_router
from app.api.invitation import router as invitation_router
from app.database.database import create_tables
from app.api.prueba import router as prueba_router
from app.modelo_ML import router as ml_router
app = FastAPI()

app.include_router(auth_router)
app.include_router(leader_router)
app.include_router(collaborator_router)
app.include_router(invitation_router)
app.include_router(prueba_router)
app.include_router(ml_router)

@app.on_event("startup")
def on_startup():
    create_tables()