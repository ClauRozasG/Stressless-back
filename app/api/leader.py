from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.models import Colaborador, Lider, LiderColaborador, PreColaborador, Invitacion
from app.database.database import get_session
from pydantic import BaseModel
from app.auth.jwt import create_access_token, verify_token
import bcrypt
from datetime import date
import random

router = APIRouter()

@router.post("/leaders")
def createLeader(data:Lider, session:Session = Depends(get_session)):

    consulta = select(Lider).where(Lider.correo == data.correo)
    resultado = session.exec(consulta).first()

    if resultado:
        raise HTTPException(status_code=401, detail="Lider ya se encuentra registrado")
    
    data.contrasenia = bcrypt.hashpw(data.contrasenia.encode(),bcrypt.gensalt()).decode("utf-8")

    session.add(data)
    session.commit()
    session.refresh(data)
    ##procesar_precolaboradores_para_lider(data, session)
    return data



def procesar_precolaboradores_para_lider(nuevo_lider, session):
    precolabs = session.exec(
        select(PreColaborador).where(PreColaborador.correo_lider == nuevo_lider.correo)
    ).all()

    for precolab in precolabs:
        codigo = str(random.randint(10000, 99999))

        invitacion = Invitacion(
            fecha_envio=date.today(),
            fecha_respuesta=date.today(),
            estado=False,
            codigo=codigo
        )
        session.add(invitacion)
        session.commit()
        session.refresh(invitacion)

        relacion = LiderColaborador(
            id_lider=nuevo_lider.id,
            id_colaborador=None,
            estado="pendiente",
            id_invitacion=invitacion.id,
            fecha_inicio=date.today(),
            fecha_fin=date.today()
        )
        session.add(relacion)

        print(f"📩 Enviando a {precolab.correo} el código {codigo} desde el líder {nuevo_lider.nombre}")

    session.commit()

@router.get("/leaders")
def getLeaders(session: Session = Depends(get_session), token = Depends(verify_token)):

    consulta = select(Lider).where(Lider.estado == True)
    resultado = session.exec(consulta).all()
    
    return resultado

@router.put("/leaders/{leaders_id}")
def update_leader(leaders_id: int, valor: Lider, session: Session = Depends(get_session), token = Depends(verify_token)):

    consulta = select(Lider).where(Lider.id == leaders_id)
    resultado = session.exec(consulta).first()

    if not resultado:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    valor.contrasenia = bcrypt.hashpw(valor.contrasenia.encode(),bcrypt.gensalt()).decode("utf-8")

    datos_dict = valor.dict(exclude_unset=True)

    for key,value in datos_dict.items():
        setattr(resultado,key,value)

    session.add(resultado)
    session.commit()
    session.refresh(resultado)

    return resultado

@router.delete("/leaders/{leaders_id}")
def delete_leader(leaders_id: int, session:Session = Depends(get_session), token = Depends(verify_token)):

    consulta = select(Lider).where(Lider.id == leaders_id)
    resultado = session.exec(consulta).first()

    if not resultado:
        raise HTTPException(status_code=401, detail="Lider no encontrado")
    
    resultado.estado = False

    session.add(resultado)
    session.commit()
    session.refresh(resultado)

    return resultado

@router.get("/leaders/{leaders_id}/collaborators")
def getCollaboratorsByLeaderId(leaders_id:int, session:Session = Depends(get_session)):

    consulta_lider = select(Lider).where(Lider.id == leaders_id)
    resultado = session.exec(consulta_lider).all()

    if not resultado:
        raise HTTPException(status_code=401, detail="Lider no encontrado")
    
    consulta = select(Colaborador).join(LiderColaborador,LiderColaborador.id_colaborador == Colaborador.id).where(LiderColaborador.id_lider == leaders_id)
    colaboradores = session.exec(consulta).all()
    
    return colaboradores


@router.get("/leaders/{leaders_id}/resumen-colaboradores")
def getResumenColaboradores(leaders_id: int, session: Session = Depends(get_session)):
    lider = session.exec(select(Lider).where(Lider.id == leaders_id)).first()
    if not lider:
        raise HTTPException(status_code=404, detail="Líder no encontrado")

    # 1) Base: todos los precolaboradores invitados por el líder
    precolabs = session.exec(
        select(PreColaborador).where(PreColaborador.correo_lider == lider.correo)
    ).all()

    resultado = []
    correos_listados = set()

    for pre in precolabs:
        
        invit_ids = session.exec(
            select(Invitacion.id).where(Invitacion.id_precolaborador == pre.id)
        ).all()
        invit_ids = [iid for (iid,) in invit_ids] if invit_ids and isinstance(invit_ids[0], tuple) else invit_ids

        
        relacion = session.exec(
            select(LiderColaborador).where(
                LiderColaborador.id_lider == lider.id,
                (LiderColaborador.id_invitacion.in_(invit_ids)) 
            )
        ).first()

        estado = "No registrado"
        colaborador_id = None
        tiene_historial = False

       
        if not relacion:
            relacion = session.exec(
                select(LiderColaborador)
                .join(Colaborador, Colaborador.id == LiderColaborador.id_colaborador)
                .where(
                    LiderColaborador.id_lider == lider.id,
                    Colaborador.correo == pre.correo
                )
            ).first()

        if relacion and relacion.id_colaborador:
            estado = "Registrado"
            colaborador_id = relacion.id_colaborador
            from app.models.models import ResultadoAnalisis
            historial = session.exec(
                select(ResultadoAnalisis).where(ResultadoAnalisis.id_colaborador == colaborador_id)
            ).first()
            tiene_historial = historial is not None

        resultado.append({
            "nombre": pre.nombre,
            "correo": pre.correo,
            "estado": estado,
            "colaborador_id": colaborador_id,
            "tiene_historial": tiene_historial
        })
        correos_listados.add(pre.correo)

    
    vinculados = session.exec(
        select(Colaborador)
        .join(LiderColaborador, LiderColaborador.id_colaborador == Colaborador.id)
        .where(LiderColaborador.id_lider == lider.id)
    ).all()

    for col in vinculados:
        if col.correo in correos_listados:
            continue  
        resultado.append({
            "nombre": col.nombre,
            "correo": col.correo,
            "estado": "Registrado",
            "colaborador_id": col.id,
            "tiene_historial": bool(col.prueba_colaborador_link)  # rápido; o consulta ResultadoAnalisis si prefieres
        })

    return resultado

