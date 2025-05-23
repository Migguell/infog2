from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid

from app.database.connection import get_db
from app.product import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("/create", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_route(
    product_data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_product = services.create_product(db, product_data)
    return db_product

@router.get("/read", response_model=List[schemas.ProductResponse])
def read_products_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    gender_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    available_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    products = services.get_products(db, skip=skip, limit=limit, category_id=category_id,
                                     gender_id=gender_id, min_price=min_price,
                                     max_price=max_price, available_only=available_only)
    return products

@router.get("/read/{product_id}", response_model=schemas.ProductResponse)
def read_product_route(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_product = services.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return db_product

@router.put("/update/{product_id}", response_model=schemas.ProductResponse)
def update_product_route(
    product_id: uuid.UUID,
    product_data: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_product = services.update_product(db, product_id, product_data)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return db_product

@router.delete("/delete/{product_id}", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
def delete_product_route(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    success = services.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return {"message": f"Produto com ID {product_id} deletado com sucesso."}