from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import models
from app.size import schemas
from typing import List, Optional

def get_size_by_name(db: Session, name: str) -> Optional[models.Size]:
    return db.query(models.Size).filter(models.Size.name == name).first()

def create_size(db: Session, size_data: schemas.SizeCreate) -> models.Size:
    if get_size_by_name(db, size_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tamanho com este nome já existe."
        )

    db_size = models.Size(
        name=size_data.name,
        long_name=size_data.long_name
    )
    db.add(db_size)
    db.commit()
    db.refresh(db_size)
    return db_size

def get_sizes(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Size]:
    return db.query(models.Size).offset(skip).limit(limit).all()

def get_size(db: Session, size_id: int) -> Optional[models.Size]:
    return db.query(models.Size).filter(models.Size.id == size_id).first()

def update_size(db: Session, size_id: int, size_data: schemas.SizeUpdate) -> Optional[models.Size]:
    db_size = get_size(db, size_id)
    if not db_size:
        return None

    update_data = size_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != db_size.name:
        if get_size_by_name(db, update_data["name"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novo nome de tamanho já existe."
            )

    for key, value in update_data.items():
        setattr(db_size, key, value)

    db.add(db_size)
    db.commit()
    db.refresh(db_size)
    return db_size

def delete_size(db: Session, size_id: int) -> bool:
    db_size = get_size(db, size_id)
    if not db_size:
        return False
    db.delete(db_size)
    db.commit()
    return True

