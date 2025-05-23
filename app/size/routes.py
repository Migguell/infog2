from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from app.database.connection import get_db
from app.size import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/sizes",
    tags=["Tamanhos"]
)

@router.post("/create", response_model=schemas.SizeResponse, status_code=status.HTTP_201_CREATED)
def create_size_route(
    size_data: schemas.SizeCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_size = services.create_size(db, size_data)
    return db_size

@router.get("/read", response_model=List[schemas.SizeResponse])
def read_sizes_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    sizes = services.get_sizes(db, skip=skip, limit=limit)
    return sizes

@router.get("/read/{size_id}", response_model=schemas.SizeResponse)
def read_size_route(
    size_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_size = services.get_size(db, size_id)
    if db_size is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tamanho não encontrado")
    return db_size

@router.put("/update/{size_id}", response_model=schemas.SizeResponse)
def update_size_route(
    size_id: int,
    size_data: schemas.SizeUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_size = services.update_size(db, size_id, size_data)
    if db_size is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tamanho não encontrado")
    return db_size

@router.delete("/delete/{size_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_size_route(
    size_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    success = services.delete_size(db, size_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tamanho não encontrado")
    return

