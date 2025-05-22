from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import models
from app.product_images import schemas
from typing import List, Optional
import uuid

def create_product_image(db: Session, image_data: schemas.ProductImageCreate) -> models.ProductImage:
    db_image = models.ProductImage(
        product_id=image_data.product_id,
        url=image_data.url,
        description=image_data.description,
        is_main=image_data.is_main
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def get_product_images(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[uuid.UUID] = None
) -> List[models.ProductImage]:
    query = db.query(models.ProductImage)
    if product_id:
        query = query.filter(models.ProductImage.product_id == product_id)
    return query.offset(skip).limit(limit).all()

def get_product_image(db: Session, image_id: uuid.UUID) -> Optional[models.ProductImage]:
    return db.query(models.ProductImage).filter(models.ProductImage.id == image_id).first()

def update_product_image(db: Session, image_id: uuid.UUID, image_data: schemas.ProductImageUpdate) -> Optional[models.ProductImage]:
    db_image = get_product_image(db, image_id)
    if not db_image:
        return None

    update_data = image_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_image, key, value)

    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def delete_product_image(db: Session, image_id: uuid.UUID) -> bool:
    db_image = get_product_image(db, image_id)
    if not db_image:
        return False
    db.delete(db_image)
    db.commit()
    return True

