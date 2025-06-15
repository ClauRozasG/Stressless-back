from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from sqlmodel import Session
from app.database.database import get_session
from datetime import datetime
import shutil
import os
import uuid  

from app.predictor import predecir_estres
from app.models.models import ResultadoAnalisis

router = APIRouter()

@router.post("/predecir/")
async def predecir_audio(
    id_colaborador: int = Form(...),
    audio: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    print("🟢 ID recibido:", id_colaborador)
    print("🟢 Archivo recibido:", audio.filename)

    try:
        # Asegurar carpeta
        os.makedirs("audios", exist_ok=True)

        # Crear nombre único
        filename = f"{uuid.uuid4()}.wav"
        file_path = os.path.join("audios", filename)

        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Predecir
        resultado = predecir_estres(file_path)

        # Guardar en DB
        nuevo_resultado = ResultadoAnalisis(
            id_colaborador=id_colaborador,
            resultado=resultado,
            fecha=datetime.utcnow(),
            archivo_audio=filename  
        )
        session.add(nuevo_resultado)
        session.commit()

        return {
            "resultado": resultado,
            "fecha": nuevo_resultado.fecha.strftime("%Y-%m-%d %H:%M"),
            "archivo": filename
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en predicción: {str(e)}")
