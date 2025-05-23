from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Verifique se ainda é necessário se /login agora usa JSON
from sqlalchemy.orm import Session
from typing import Annotated
# from datetime import timedelta # Esta importação pode ser removida se não usada diretamente aqui

from app.database.connection import get_db
from app.auth import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, create_token_response # Importar de dependencies

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user_route(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = services.register_user(db, user_data)
    return db_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    user_login: schemas.UserLogin, # Assumindo que você já fez a mudança para JSON aqui
    db: Session = Depends(get_db)
):
    user = services.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Chama a função de criação de token do novo módulo JWT
    return create_token_response(subject_id=user.id, is_admin=user.is_admin)

@router.post("/refresh-token", response_model=schemas.Token)
def refresh_access_token(
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db) # db é injeção, não o current_user
):
    # Chama a função de criação de token do novo módulo JWT
    return create_token_response(subject_id=current_user.id, is_admin=current_user.is_admin)

