from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.models import Colaborador
from app.database.database import get_session
from pydantic import BaseModel
from app.auth.jwt import create_access_token, verify_token
from sqlalchemy import func
import bcrypt

router = APIRouter()

@router.post("/collaborators")
def createCollaborator(data:Colaborador, session: Session = Depends(get_session)):
    
    consulta = select(Colaborador).where(Colaborador.correo == data.correo)
    resultado = session.exec(consulta).first()

    if resultado:
        raise HTTPException(status_code=401, detail="Colaborador ya se encuentra registrado")
    
    data.contrasenia = bcrypt.hashpw(data.contrasenia.encode(),bcrypt.gensalt()).decode("utf-8")

    session.add(data)
    session.commit()
    session.refresh(data)

    return data

@router.get("/collaborators")
def getCollaborators(session: Session = Depends(get_session), token = Depends(verify_token)):

    consulta = select(Colaborador).where(Colaborador.estado == True)
    resultado = session.exec(consulta).all()
    
    return resultado

@router.get("/collaborators/{collaborators_name}")
def getCollaboratorByName(collaborators_name:str, session:Session = Depends(get_session), token=Depends(verify_token)):

    #consulta = select(Colaborador).like(f"%{collaborators_name}").all()
    return session.query(Colaborador).filter(func.lower(Colaborador.nombre).like(f"%{collaborators_name.lower()}%")).all()
    #resultado = session.exec(consulta).all()

    #return resultado

@router.put("/collaborators/{collaborators_id}")
def update_collaborator(collaborators_id: int, valor: Colaborador, session: Session = Depends(get_session), token = Depends(verify_token)):

    consulta = select(Colaborador).where(Colaborador.id == collaborators_id)
    resultado = session.exec(consulta).first()

    if not resultado:
        raise HTTPException(status_code=401, detail="Colaborador no encontrado")
    
    valor.contrasenia = bcrypt.hashpw(valor.contrasenia.encode(),bcrypt.gensalt()).decode("utf-8")

    datos_dict = valor.dict(exclude_unset=True)

    for key,value in datos_dict.items():
        setattr(resultado,key,value)

    session.add(resultado)
    session.commit()
    session.refresh(resultado)

    return resultado

@router.delete("/collaborators/{collaborators_id}")
def delete_collaborator(collaborators_id: int, session: Session = Depends(get_session), token = Depends(verify_token)):

    consulta = select(Colaborador).where(Colaborador.id == collaborators_id)
    resultado = session.exec(consulta).first()

    if not resultado:
        raise HTTPException(status_code=401, detail="Colaborador no encontrado")
    
    resultado.estado = False

    session.add(resultado)
    session.commit()
    session.refresh(resultado)

    return resultado