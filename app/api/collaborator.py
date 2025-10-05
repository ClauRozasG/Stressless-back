from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.models import Colaborador, Lider, Prueba, Notificacion, NotificacionLider, LiderColaborador
from app.database.database import get_session
from pydantic import BaseModel
from app.auth.jwt import create_access_token, verify_token
from sqlalchemy import func
import bcrypt
from datetime import datetime

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


@router.get("/colaborador/{id}/datos")
def obtener_datos_colaborador(id: int, session: Session = Depends(get_session)):
    colaborador = session.get(Colaborador, id)
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    if not colaborador.lideres_link:
        raise HTTPException(status_code=404, detail="El colaborador no tiene líder asignado")

    id_lider = colaborador.lideres_link[0].id_lider  
    lider = session.get(Lider, id_lider)

    if not lider:
        raise HTTPException(status_code=404, detail="Líder no encontrado")

    return {
        "correo": colaborador.correo,
        "nombre_lider": lider.nombre
    }


class CambioContrasenaRequest(BaseModel):
    nueva_contrasena: str



@router.put("/colaborador/{id}/cambiar-contrasena")
def cambiar_contrasena(id: int, data: CambioContrasenaRequest, session: Session = Depends(get_session)):
    colaborador = session.get(Colaborador, id)
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    hash = bcrypt.hashpw(data.nueva_contrasena.encode('utf-8'), bcrypt.gensalt())
    colaborador.contrasenia = hash.decode('utf-8') 
    session.add(colaborador)
    session.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


@router.get("/colaborador/{id}/prueba-pendiente")
def obtener_prueba_pendiente(id: int, session: Session = Depends(get_session)):
    """
    Devuelve la siguiente PRUEBA pendiente (FIFO) del colaborador.
    Ya no depende de notificaciones.leido.
    """
    # Trae la PRIMERA prueba pendiente por fecha_registro ASC (o por id ASC)
    prueba = session.exec(
        select(Prueba)
        .where(Prueba.id_colaborador == id, Prueba.estado == 0)
        .order_by(Prueba.fecha_registro.asc(), Prueba.id.asc())
    ).first()

    if not prueba:
        return {"pendiente": False}

    
    notificacion = session.exec(
        select(Notificacion).where(Notificacion.id_prueba == prueba.id)
        .order_by(Notificacion.id.asc(), Notificacion.id.asc())
    ).first()

    return {
        "pendiente": True,
        "id_prueba": prueba.id,
        "id_notificacion": notificacion.id if notificacion else None,
        "fecha": (prueba.fecha_registro.isoformat()
                  if hasattr(prueba.fecha_registro, "isoformat")
                  else str(prueba.fecha_registro))
    }


@router.put("/colaborador/{id}/completar-prueba")
def completar_prueba(id: int, resultado: bool, session: Session = Depends(get_session)):
    # 1) Tomar la PRIMERA prueba pendiente del colaborador (FIFO)
    prueba = session.exec(
        select(Prueba).where(
            Prueba.id_colaborador == id,
            Prueba.estado == 0
        ).order_by(Prueba.fecha_registro.asc(), Prueba.id.asc())
    ).first()

    if not prueba:
        raise HTTPException(status_code=404, detail="No hay prueba pendiente")

    # 2) Completar prueba
    prueba.estado = 1
    prueba.resultado = resultado
    prueba.fecha_resultado = datetime.now()
    session.add(prueba)
    session.commit()

    # 3) Marcar notificaciones de esa prueba como leídas
    notis = session.exec(
        select(Notificacion).where(Notificacion.id_prueba == prueba.id)
    ).all()
    for n in notis:
        if not n.leido:
            n.leido = True
            session.add(n)
    session.commit()

    
    ultimas = session.exec(
        select(Prueba)
        .where(Prueba.id_colaborador == id, Prueba.estado == 1)
        .order_by(Prueba.fecha_resultado.desc())
        .limit(3)
    ).all()

    if len(ultimas) == 3 and all(p.resultado is True for p in ultimas):
        rel = session.exec(
            select(LiderColaborador)
            .where(LiderColaborador.id_colaborador == id, LiderColaborador.estado == "activo")
        ).first()

        if rel:
            col = session.get(Colaborador, id)
            mensaje = f"El colaborador {col.nombre if col else id} tiene 3 resultados consecutivos de estrés."
            tercera = ultimas[-1].fecha_resultado  

            ya_existe = session.exec(
                select(NotificacionLider)
                .where(
                    NotificacionLider.id_lider == rel.id_lider,
                    NotificacionLider.id_colaborador == id,
                    NotificacionLider.consecutivas >= 3,
                    NotificacionLider.creado_en >= tercera
                )
            ).first()

            if not ya_existe:
                nl = NotificacionLider(
                    id_lider=rel.id_lider,
                    id_colaborador=id,
                    consecutivas=3,
                    mensaje=mensaje,
                    leido=False
                )
                session.add(nl)
                session.commit()

    # 5) Respuesta
    return {"mensaje": "Prueba completada correctamente"}

@router.get("/colaborador/{id}/pruebas-pendientes")
def listar_pruebas_pendientes(id: int, session: Session = Depends(get_session)):
    """
    Devuelve TODAS las pruebas pendientes del colaborador en orden FIFO.
    """
    pendientes = session.exec(
        select(Prueba)
        .where(Prueba.id_colaborador == id, Prueba.estado == 0)
        .order_by(Prueba.fecha_registro.asc(), Prueba.id.asc())
    ).all()

    out = []
    for p in pendientes:
        noti = session.exec(
            select(Notificacion).where(Notificacion.id_prueba == p.id)
            .order_by(Notificacion.fecha_registro.asc(), Notificacion.id.asc())
        ).first()
        out.append({
            "id_prueba": p.id,
            "id_notificacion": noti.id if noti else None,
            "fecha": (p.fecha_registro.isoformat()
                      if hasattr(p.fecha_registro, "isoformat")
                      else str(p.fecha_registro))
        })
    return {"total": len(out), "items": out}



