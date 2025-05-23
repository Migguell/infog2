from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone # timedelta ainda é necessário para o timedelta(minutes=...)
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from app.core.config import get_settings
from app.database import models
from app.auth import schemas
from typing import Optional
import uuid

# create_token_response e create_access_token foram movidos para app/core/dependencies.py

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def register_user(db: Session, user_data: schemas.UserCreate) -> models.User:
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado."
        )
    if db.query(models.User).filter(models.User.cpf == user_data.cpf).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já registrado."
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        name=user_data.name,
        cpf=user_data.cpf,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

