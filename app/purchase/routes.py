from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid
from datetime import datetime

from app.database.connection import get_db
from app.purchase import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/purchases",
    tags=["Pedidos"]
)

@router.post("/create", response_model=schemas.PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_route(
    purchase_data: schemas.PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_purchase = services.create_purchase(db, purchase_data)
    return db_purchase

@router.get("/read", response_model=List[schemas.PurchaseResponse])
def read_purchases_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    client_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    product_section_category_id: Optional[int] = Query(None),
    product_section_gender_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    purchases = services.get_purchases(db, skip=skip, limit=limit, client_id=client_id,
                                       status=status, start_date=start_date, end_date=end_date,
                                       product_section_category_id=product_section_category_id,
                                       product_section_gender_id=product_section_gender_id)
    return purchases

@router.get("/read/{purchase_id}", response_model=schemas.PurchaseResponse)
def read_purchase_route(
    purchase_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_purchase = services.get_purchase(db, purchase_id)
    if db_purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return db_purchase

@router.put("/update/{purchase_id}", response_model=schemas.PurchaseResponse)
def update_purchase_route(
    purchase_id: uuid.UUID,
    purchase_data: schemas.PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_purchase = services.update_purchase(db, purchase_id, purchase_data)
    if db_purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return db_purchase

@router.delete("/delete/{purchase_id}", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
def delete_purchase_route(
    purchase_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    success = services.delete_purchase(db, purchase_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return {"message": f"Pedido com ID {purchase_id} deletado com sucesso."}