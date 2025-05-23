from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from app.core.config import get_settings
from app.database import models
from app.auth import schemas
from typing import Optional
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

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

def create_token_response(user: models.User) -> schemas.Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "is_admin": user.is_admin}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")
