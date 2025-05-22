from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.database import models
from app.clients import schemas
from typing import List, Optional
import uuid

def get_client_by_email(db: Session, email: str) -> Optional[models.Client]:
    return db.query(models.Client).filter(models.Client.email == email).first()

def get_client_by_cpf(db: Session, cpf: str) -> Optional[models.Client]:
    return db.query(models.Client).filter(models.Client.cpf == cpf).first()

def create_client(db: Session, client_data: schemas.ClientCreate) -> models.Client:
    if get_client_by_email(db, client_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado."
        )
    if get_client_by_cpf(db, client_data.cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já registrado."
        )

    db_client = models.Client(
        name=client_data.name,
        email=client_data.email,
        cpf=client_data.cpf,
        address=client_data.address
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_clients(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    email: Optional[str] = None
) -> List[models.Client]:
    query = db.query(models.Client)
    if name:
        query = query.filter(models.Client.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(models.Client.email.ilike(f"%{email}%"))
    return query.offset(skip).limit(limit).all()

def get_client(db: Session, client_id: uuid.UUID) -> Optional[models.Client]:
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def update_client(db: Session, client_id: uuid.UUID, client_data: schemas.ClientUpdate) -> Optional[models.Client]:
    db_client = get_client(db, client_id)
    if not db_client:
        return None

    update_data = client_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != db_client.email:
        if get_client_by_email(db, update_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novo email já registrado por outro cliente."
            )
    if "cpf" in update_data and update_data["cpf"] != db_client.cpf:
        if get_client_by_cpf(db, update_data["cpf"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novo CPF já registrado por outro cliente."
            )

    for key, value in update_data.items():
        setattr(db_client, key, value)

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: uuid.UUID) -> bool:
    db_client = get_client(db, client_id)
    if not db_client:
        return False
    db.delete(db_client)
    db.commit()
    return True

