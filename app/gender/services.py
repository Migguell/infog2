from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import models
from app.genders import schemas
from typing import List, Optional

def get_gender_by_name(db: Session, name: str) -> Optional[models.Gender]:
    return db.query(models.Gender).filter(models.Gender.name == name).first()

def create_gender(db: Session, gender_data: schemas.GenderCreate) -> models.Gender:
    if get_gender_by_name(db, gender_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gênero com este nome já existe."
        )

    db_gender = models.Gender(
        name=gender_data.name,
        long_name=gender_data.long_name
    )
    db.add(db_gender)
    db.commit()
    db.refresh(db_gender)
    return db_gender

def get_genders(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Gender]:
    return db.query(models.Gender).offset(skip).limit(limit).all()

def get_gender(db: Session, gender_id: int) -> Optional[models.Gender]:
    return db.query(models.Gender).filter(models.Gender.id == gender_id).first()

def update_gender(db: Session, gender_id: int, gender_data: schemas.GenderUpdate) -> Optional[models.Gender]:
    db_gender = get_gender(db, gender_id)
    if not db_gender:
        return None

    update_data = gender_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != db_gender.name:
        if get_gender_by_name(db, update_data["name"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novo nome de gênero já existe."
            )

    for key, value in update_data.items():
        setattr(db_gender, key, value)

    db.add(db_gender)
    db.commit()
    db.refresh(db_gender)
    return db_gender

def delete_gender(db: Session, gender_id: int) -> bool:
    db_gender = get_gender(db, gender_id)
    if not db_gender:
        return False
    db.delete(db_gender)
    db.commit()
    return True

