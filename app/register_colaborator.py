from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
#from database import get_session
from app.models.models import Colaborador, Invitacion, LiderColaborador, Lider, PreColaborador
import bcrypt
from datetime import date
from sqlalchemy import and_
from app.database.database import get_session


router = APIRouter()

class RegisterColaboradorRequest(BaseModel):
    nombre: str
    correo: str
    contrasenia: str
    codigo: str

@router.post("/register-colaborador")
def register_colaborador(data: RegisterColaboradorRequest, session: Session = Depends(get_session)):
    # Buscar invitación por código
    invitacion = session.exec(select(Invitacion).where(Invitacion.codigo == data.codigo)).first()
    if not invitacion or invitacion.estado:
        raise HTTPException(status_code=404, detail="Código inválido o ya usado")

    # Crear colaborador
    hashed_pw = bcrypt.hashpw(data.contrasenia.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    colaborador = Colaborador(
        nombre=data.nombre,
        correo=data.correo,
        contrasenia=hashed_pw,
        estado=True
    )
    session.add(colaborador)
    session.commit()
    session.refresh(colaborador)

    # Actualizar relación en LiderColaborador
    relacion = session.exec(
        select(LiderColaborador).where(LiderColaborador.id_invitacion == invitacion.id)
    ).first()

    if not relacion:
        raise HTTPException(status_code=404, detail="No se encontró relación líder-colaborador para esta invitación")

    relacion.id_colaborador = colaborador.id
    relacion.estado = "activo"
    relacion.fecha_inicio = date.today()
    relacion.fecha_fin = date.today() 

    # Marcar invitación como usada
    invitacion.estado = True
    invitacion.fecha_respuesta = date.today()

    session.commit()

    return colaborador



@router.get("/validar-codigo/{codigo}")
def validar_codigo(codigo: str, session: Session = Depends(get_session)):
    print("📦 Código recibido:", codigo)
    print("📦 Tipo del código:", type(codigo))
    invitacion = session.exec(
    select(Invitacion).where(
        and_(Invitacion.codigo == str(codigo), Invitacion.estado == False)
    )
).first()

    if not invitacion:
        raise HTTPException(status_code=404, detail="Código inválido o ya usado")

    relacion = session.exec(
        select(LiderColaborador).where(LiderColaborador.id_invitacion == invitacion.id)
    ).first()

    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")

    # Buscar precolaborador por correo y líder
    lider = session.exec(
        select(Lider).where(Lider.id == relacion.id_lider)
    ).first()

    precolab = session.exec(
        select(PreColaborador).where(PreColaborador.id == invitacion.id_precolaborador)
    ).first()

    return {
        "nombre": precolab.nombre,
        "correo": precolab.correo,
        "id_lider": relacion.id_lider,
        "correo_lider": lider.correo
    }

