from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.database import models
from app.product import schemas
from typing import List, Optional
import uuid

def get_product_by_name(db: Session, name: str) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.name == name).first()

def create_product(db: Session, product_data: schemas.ProductCreate) -> models.Product:
    if get_product_by_name(db, product_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produto com este nome já existe."
        )

    db_product = models.Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        inventory=product_data.inventory,
        size_id=product_data.size_id,
        category_id=product_data.category_id,
        gender_id=product_data.gender_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    if product_data.product_image_ids:
        existing_images = db.query(models.ProductImage).filter(
            models.ProductImage.id.in_(product_data.product_image_ids)
        ).all()

        if len(existing_images) != len(product_data.product_image_ids):
            found_ids = {str(img.id) for img in existing_images}
            missing_ids = [str(uid) for uid in product_data.product_image_ids if str(uid) not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Algumas imagens com IDs fornecidos não foram encontradas: {', '.join(missing_ids)}"
            )
        
        for img in existing_images:
            img.product_id = db_product.id
            db.add(img)

        db.commit() 
        db.refresh(db_product) 

    return db_product

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    gender_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = False
) -> List[models.Product]:
    query = db.query(models.Product).options(joinedload(models.Product.images))
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if gender_id:
        query = query.filter(models.Product.gender_id == gender_id)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    if available_only:
        query = query.filter(models.Product.inventory > 0)
    return query.offset(skip).limit(limit).all()

def get_product(db: Session, product_id: uuid.UUID) -> Optional[models.Product]:
    return db.query(models.Product).options(joinedload(models.Product.images)).filter(models.Product.id == product_id).first()

def update_product(db: Session, product_id: uuid.UUID, product_data: schemas.ProductUpdate) -> Optional[models.Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    update_data = product_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != db_product.name:
        if get_product_by_name(db, update_data["name"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novo nome de produto já existe."
            )

    for key, value in update_data.items():
        if key != "product_image_ids":
            setattr(db_product, key, value)

    if "product_image_ids" in update_data:
        new_image_ids_set = set(update_data["product_image_ids"] or [])
        
        current_associated_image_ids = {img.id for img in db_product.images}

        images_to_delete_from_product = db.query(models.ProductImage).filter(
            models.ProductImage.product_id == product_id,
            models.ProductImage.id.notin_(new_image_ids_set)
        ).all()

        for img_to_delete in images_to_delete_from_product:
            db.delete(img_to_delete)

        if new_image_ids_set:
            images_to_associate = db.query(models.ProductImage).filter(
                models.ProductImage.id.in_(list(new_image_ids_set))
            ).all()

            found_ids = {str(img.id) for img in images_to_associate}
            missing_ids = [str(uid) for uid in new_image_ids_set if str(uid) not in found_ids]
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Algumas imagens com IDs fornecidos para atualização não foram encontradas: {', '.join(missing_ids)}"
                )
            
            for img in images_to_associate:
                if img.product_id != product_id:
                    img.product_id = product_id
                    db.add(img)
        
        db.commit()
        db.refresh(db_product)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: uuid.UUID) -> bool:
    db_product = get_product(db, product_id)
    if not db_product:
        return False
    
    db.query(models.ProductImage).filter(models.ProductImage.product_id == product_id).delete(synchronize_session='fetch')
    
    db.delete(db_product)
    db.commit()
    return True