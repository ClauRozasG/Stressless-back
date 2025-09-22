# app/auth/jwt.py
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi import Depends, HTTPException, status

# Dos esquemas: uno estricto y uno opcional
##optional_bearer = HTTPBearer(auto_error=False)

bearer_scheme = HTTPBearer()  


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
        

##def verify_token_optional(creds: HTTPAuthorizationCredentials | None = Security(optional_bearer)):
##    # Si no hay token, deja pasar (demo)
##    if not creds:
##        return None
##    # Si hay token, intenta decodificarlo
##    try:
##        return jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
##    except JWTError:
##        # En demo preferimos no botar 401; simplemente tratar como sin token
##        return None
