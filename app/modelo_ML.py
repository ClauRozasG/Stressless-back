from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from sqlmodel import Session, select
from app.database.database import get_session
from datetime import datetime
import shutil, os, uuid

from app.predictor import predecir_estres
from app.models.models import ResultadoAnalisis, Prueba, Notificacion

router = APIRouter()

@router.post("/predecir/")
async def predecir_audio(
    id_colaborador: int = Form(...),
    id_prueba: int = Form(...),
    audio: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    print("🟢 ID recibido:", id_colaborador)
    print("🟢 Archivo recibido:", audio.filename)

    if not audio or not audio.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Sube un archivo .wav válido")

    try:
        os.makedirs("audios", exist_ok=True)
        filename = f"{uuid.uuid4()}.wav"
        file_path = os.path.join("audios", filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        await audio.close()

        # Predicción
        resultado = predecir_estres(file_path)  # "Estresado" / "No estresado"
        es_estresado = (resultado == "Estresado")

        # Actualizar prueba
        prueba = session.get(Prueba, id_prueba)
        if not prueba:
            raise HTTPException(status_code=404, detail="Prueba no encontrada")

        prueba.resultado = es_estresado
        prueba.fecha_resultado = datetime.utcnow().date()
        prueba.estado = 2  # completado

        # Guardar resultado
        nuevo_resultado = ResultadoAnalisis(
            id_colaborador=id_colaborador,
            id_prueba=id_prueba,
            resultado=resultado,
            fecha=prueba.fecha_resultado,
            archivo_audio=filename
        )
        session.add(nuevo_resultado)
        session.add(prueba)
        session.commit()

        
        noti = session.exec(
            select(Notificacion).where(
                Notificacion.id_prueba == id_prueba,
                Notificacion.id_colaborador == id_colaborador
            )
        ).first()
        if not noti:
            pass
        else:
            noti.leido = True
            session.add(noti)
            session.commit()

        return {
            "resultado": resultado,
            "fecha": nuevo_resultado.fecha.strftime("%Y-%m-%d %H:%M"),
            "archivo": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error en predicción: {str(e)}")