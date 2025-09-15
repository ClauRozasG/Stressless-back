from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from app.auth.jwt import verify_token
from app.database.database import get_session
from app.models.models import Notificacion, Prueba

router = APIRouter()

class PruebaRequest(BaseModel):
    id_lider: int
    collaborators: List[int]

@router.post("/prueba")
def createPrueba(request: PruebaRequest, session: Session = Depends(get_session), token = Depends(verify_token)):
    for i in request.collaborators:
        prueba = Prueba(
            fecha_registro=datetime.now().date(),
            fecha_resultado=None,
            id_colaborador=i,
            estado=0,        
            resultado=None    
        )
        session.add(prueba)
        session.flush()  

        notificacion = Notificacion(
            id_colaborador=i,
            id_prueba=prueba.id,
            mensaje="Tienes una nueva prueba pendiente",
            leido=False
        )
        session.add(notificacion)

    session.commit()
    return {"mensaje": "Pruebas y notificaciones enviadas correctamente"}


@router.get("/historial/{id_colaborador}")
def get_historial(id_colaborador: int, session: Session = Depends(get_session)):
    resultados = session.exec(
        select(Prueba).where(Prueba.id_colaborador == id_colaborador)
    ).all()
    return [
        {
            "resultado": ("Estresado" if r.resultado else "No estresado") if r.resultado is not None else "Pendiente",
            "fecha": r.fecha_resultado.isoformat() if r.fecha_resultado else None
        }
        for r in resultados
    ]
