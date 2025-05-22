from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from app.database.connection import get_db
from app.genders import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/genders",
    tags=["Gêneros"]
)

@router.post("/create", response_model=schemas.GenderResponse, status_code=status.HTTP_201_CREATED)
def create_gender_route(
    gender_data: schemas.GenderCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_gender = services.create_gender(db, gender_data)
    return db_gender

@router.get("/read", response_model=List[schemas.GenderResponse])
def read_genders_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    genders = services.get_genders(db, skip=skip, limit=limit)
    return genders

@router.get("/read/{gender_id}", response_model=schemas.GenderResponse)
def read_gender_route(
    gender_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_gender = services.get_gender(db, gender_id)
    if db_gender is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gênero não encontrado")
    return db_gender

@router.put("/update/{gender_id}", response_model=schemas.GenderResponse)
def update_gender_route(
    gender_id: int,
    gender_data: schemas.GenderUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    db_gender = services.update_gender(db, gender_id, gender_data)
    if db_gender is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gênero não encontrado")
    return db_gender

@router.delete("/delete/{gender_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gender_route(
    gender_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)]
):
    success = services.delete_gender(db, gender_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gênero não encontrado")
    return

