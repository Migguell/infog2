from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.database import models
from app.purchases import schemas
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

def create_purchase(db: Session, purchase_data: schemas.PurchaseCreate) -> models.Purchase:
    db_client = db.query(models.Client).filter(models.Client.id == purchase_data.client_id).first()
    if not db_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )

    total_subtotal = Decimal('0.00')
    purchase_items = []

    for item_data in purchase_data.items:
        db_product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com ID {item_data.product_id} não encontrado."
            )
        if db_product.inventory < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente para o produto {db_product.name}. Disponível: {db_product.inventory}, Solicitado: {item_data.quantity}."
            )
        
        db_size = db.query(models.Size).filter(models.Size.id == item_data.size_id).first()
        if not db_size:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tamanho com ID {item_data.size_id} não encontrado."
            )

        item_total_price = item_data.quantity * item_data.unit_price_at_purchase
        total_subtotal += item_total_price

        purchase_item = models.PurchaseItem(
            product_id=item_data.product_id,
            size_id=item_data.size_id,
            quantity=item_data.quantity,
            unit_price_at_purchase=item_data.unit_price_at_purchase,
            total_price=item_total_price
        )
        purchase_items.append(purchase_item)

        db_product.inventory -= item_data.quantity
        db.add(db_product)

    db_purchase = models.Purchase(
        client_id=purchase_data.client_id,
        subtotal=total_subtotal,
        status="pending",
        items=purchase_items
    )
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

def get_purchases(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    product_section_category_id: Optional[int] = None,
    product_section_gender_id: Optional[int] = None
) -> List[models.Purchase]:
    query = db.query(models.Purchase).options(joinedload(models.Purchase.items).joinedload(models.PurchaseItem.product))

    if client_id:
        query = query.filter(models.Purchase.client_id == client_id)
    if status:
        query = query.filter(models.Purchase.status == status)
    if start_date:
        query = query.filter(models.Purchase.created_at >= start_date)
    if end_date:
        query = query.filter(models.Purchase.created_at <= end_date)
    
    if product_section_category_id or product_section_gender_id:
        query = query.join(models.Purchase.items).join(models.PurchaseItem.product)
        if product_section_category_id:
            query = query.filter(models.Product.category_id == product_section_category_id)
        if product_section_gender_id:
            query = query.filter(models.Product.gender_id == product_section_gender_id)
        query = query.distinct()

    return query.offset(skip).limit(limit).all()

def get_purchase(db: Session, purchase_id: uuid.UUID) -> Optional[models.Purchase]:
    return db.query(models.Purchase).options(joinedload(models.Purchase.items).joinedload(models.PurchaseItem.product)).filter(models.Purchase.id == purchase_id).first()

def update_purchase(db: Session, purchase_id: uuid.UUID, purchase_data: schemas.PurchaseUpdate) -> Optional[models.Purchase]:
    db_purchase = get_purchase(db, purchase_id)
    if not db_purchase:
        return None

    update_data = purchase_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_purchase, key, value)

    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

def delete_purchase(db: Session, purchase_id: uuid.UUID) -> bool:
    db_purchase = get_purchase(db, purchase_id)
    if not db_purchase:
        return False
    
    for item in db_purchase.items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if db_product:
            db_product.inventory += item.quantity
            db.add(db_product)

    db.delete(db_purchase)
    db.commit()
    return True

