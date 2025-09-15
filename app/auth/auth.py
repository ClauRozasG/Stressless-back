from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.models.models import Lider, Colaborador
from app.database.database import get_session
from pydantic import BaseModel
from app.auth.jwt import create_access_token, verify_token
from fastapi.security import OAuth2PasswordBearer
import bcrypt

router = APIRouter()

class LoginRequest(BaseModel):
    correo: str
    contrasenia: str
    rol: str

@router.post("/login")
def login(data: LoginRequest, session: Session = Depends(get_session)):

    if data.rol == "LIDER":
        consulta = select(Lider).where(Lider.correo == data.correo)
        resultado = session.exec(consulta).first()

    if data.rol == "COLABORADOR":
        consulta = select(Colaborador).where(Colaborador.correo == data.correo)
        resultado = session.exec(consulta).first()

    if not resultado:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    contrasenia_valida = bcrypt.checkpw(data.contrasenia.encode("utf-8"), resultado.contrasenia.encode("utf-8"))
    
    if not contrasenia_valida:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_access_token({"sub": data.correo, "rol": data.rol, "id": resultado.id})

    return {
        "token": token,
        "id": resultado.id,
        "nombre": resultado.nombre  
    }


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        return {
            "correo": payload.get("sub"),
            "rol": payload.get("rol")
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )