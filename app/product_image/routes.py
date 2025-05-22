from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid

from app.database.connection import get_db
from app.product_images import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/product-images",
    tags=["Imagens de Produtos"]
)

@router.post("/create", response_model=schemas.ProductImageResponse, status_code=status.HTTP_201_CREATED)
def create_product_image_route(
    image_data: schemas.ProductImageCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_image = services.create_product_image(db, image_data)
    return db_image

@router.get("/read", response_model=List[schemas.ProductImageResponse])
def read_product_images_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    product_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    images = services.get_product_images(db, skip=skip, limit=limit, product_id=product_id)
    return images

@router.get("/read/{image_id}", response_model=schemas.ProductImageResponse)
def read_product_image_route(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_image = services.get_product_image(db, image_id)
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")
    return db_image

@router.put("/update/{image_id}", response_model=schemas.ProductImageResponse)
def update_product_image_route(
    image_id: uuid.UUID,
    image_data: schemas.ProductImageUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_image = services.update_product_image(db, image_id, image_data)
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")
    return db_image

@router.delete("/delete/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image_route(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)]
):
    success = services.delete_product_image(db, image_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")
    return

