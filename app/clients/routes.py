from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid

from app.database.connection import get_db
from app.clients import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user, create_token_response

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

@router.post("/create", response_model=schemas.ClientCreateResponse, status_code=status.HTTP_201_CREATED)
def create_client_route(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db)
):
    db_client = services.create_client(db, client_data)
    
    client_response_data = {
        "id": db_client.id,
        "name": db_client.name,
        "email": db_client.email,
        "cpf": db_client.cpf,
        "created_at": db_client.created_at,
        "updated_at": db_client.updated_at,
    }

    return schemas.ClientCreateResponse(
        client=schemas.ClientResponse(**client_response_data),
        token=create_token_response(subject_id=db_client.id, is_client=True)
    )

@router.get("/read", response_model=List[schemas.ClientResponse])
def read_clients_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    clients = services.get_clients(db, skip=skip, limit=limit, name=name, email=email)
    return clients

@router.get("/read/{client_id}", response_model=schemas.ClientResponse)
def read_client_route(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_client = services.get_client(db, client_id)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return db_client

@router.put("/update/{client_id}", response_model=schemas.ClientResponse)
def update_client_route(
    client_id: uuid.UUID,
    client_data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    db_client = services.update_client(db, client_id, client_data)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return db_client

@router.delete("/delete/{client_id}", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
def delete_client_route(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    success = services.delete_client(db, client_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    
    return {"message": f"Cliente com ID {client_id} deletado com sucesso."}