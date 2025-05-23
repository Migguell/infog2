from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Annotated, Optional, Union
from datetime import datetime, timedelta, timezone # Adicionado para funções de criação de token
import uuid # Necessário para uuid.UUID

from app.core.config import get_settings
from app.database.connection import get_db
from app.auth import schemas
from app.database import models

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT de acesso."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_token_response(subject_id: Union[str, uuid.UUID], is_admin: bool = False, is_client: bool = False) -> schemas.Token:
    """
    Cria a resposta do token JWT para um sujeito (usuário ou cliente).
    Recebe o ID do sujeito e suas permissões para gerar o token.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Prepara os dados do payload do token
    token_data = {"sub": str(subject_id)}
    if is_admin:
        token_data["is_admin"] = True
    if is_client:
        token_data["is_client"] = True # Adiciona um flag para identificar se é um token de cliente

    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=uuid.UUID(user_id))
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo")
    return current_user

async def get_current_admin_user(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de administrador."
        )
    return current_user

