from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session
from app.auth.jwt import verify_token
from app.database.database import get_session
from app.models.models import Notificacion, Prueba

router = APIRouter()

class PruebaRequest(BaseModel):
    id_lider:int
    collaborators:List[int]

@router.post("/prueba")
def createPrueba(request:PruebaRequest, session:Session = Depends(get_session), token = Depends(verify_token)):

    for i in request.collaborators:
        prueba:Prueba = Prueba(
            fecha_registro=datetime.now(),
            fecha_resultado=None,
            id_colaborador=i,
            estado=1,
            resultado=True,
        )
        session.add(prueba)
        session.commit()
        session.refresh(prueba)
        
        notificacion:Notificacion = Notificacion(
            descripcion="Notificacion",
            estado="Pendiente",
            fecha_envio=datetime.now(),
            id_prueba=prueba.id,
        )
        session.add(notificacion),
        session.commit()
        session.refresh(notificacion)

    return {"prueba":prueba,"notificacion":notificacion}