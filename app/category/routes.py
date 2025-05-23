from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from app.database.connection import get_db
from app.category import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/categories",
    tags=["Category"]
)

@router.post("/create", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category_route(
    category_data: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_category = services.create_category(db, category_data)
    return db_category

@router.get("/read", response_model=List[schemas.CategoryResponse])
def read_categories_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    categories = services.get_categories(db, skip=skip, limit=limit)
    return categories

@router.get("/read/{category_id}", response_model=schemas.CategoryResponse)
def read_category_route(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_category = services.get_category(db, category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return db_category

@router.put("/update/{category_id}", response_model=schemas.CategoryResponse)
def update_category_route(
    category_id: int,
    category_data: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_category = services.update_category(db, category_id, category_data)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return db_category

@router.delete("/delete/{category_id}", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
def delete_category_route(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    success = services.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return {"message": f"Categoria com ID {category_id} deletada com sucesso."}