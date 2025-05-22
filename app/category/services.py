from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import models
from app.categories import schemas
from typing import List, Optional

def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.name == name).first()

def create_category(db: Session, category_data: schemas.CategoryCreate) -> models.Category:
    if get_category_by_name(db, category_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria com este nome já existe."
        )

    db_category = models.Category(
        name=category_data.name
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_categories(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Category]:
    return db.query(models.Category).offset(skip).limit(limit).all()

def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def update_category(db: Session, category_id: int, category_data: schemas.CategoryUpdate) -> Optional[models.Category]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None

    update_data = category_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != db_category.name:
        if get_category_by_name(db, update_data["name"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novo nome de categoria já existe."
            )

    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> bool:
    db_category = get_category(db, category_id)
    if not db_category:
        return False
    db.delete(db_category)
    db.commit()
    return True

