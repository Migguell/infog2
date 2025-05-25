from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid
from datetime import datetime

from app.database.connection import get_db
from app.purchase import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.purchase.schemas import MessageResponse as PurchaseMessageResponse

router = APIRouter(
    prefix="/purchases",
    tags=["Pedidos"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida, estoque insuficiente, ou erro de validação."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado."},
        status.HTTP_404_NOT_FOUND: {"description": "Pedido, cliente ou produto não encontrado."},
    }
)

@router.post(
    "/create",
    response_model=schemas.PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pedido.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Pedido criado com sucesso.",
            "content": {"application/json": {"example": schemas.PurchaseResponse.model_config['json_schema_extra']['example'] if schemas.PurchaseResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_400_BAD_REQUEST: {"content": {"application/json": {"example": {"detail": "Estoque insuficiente para o produto X."}}}},
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Cliente não encontrado."}}}}
    }
)
def create_purchase_route(
    purchase_data: schemas.PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Cria novo pedido para cliente com lista de itens. Deduz do inventário.
    - **Regras de negócio**:
        - `client_id` existente. `product_id` e `size_id` nos itens existentes.
        - Estoque suficiente. Status inicial 'pending'. Requer auth.
    - **Casos de uso**: Cliente finalizando compra. Vendedor criando pedido.
    """
    return services.create_purchase(db, purchase_data)

@router.get(
    "/read",
    response_model=List[schemas.PurchaseResponse],
    summary="Lista pedidos com filtros e paginação.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de pedidos retornada.",
            "content": {"application/json": {"example": [
                schemas.PurchaseResponse.model_config['json_schema_extra']['example'] if schemas.PurchaseResponse.model_config.get('json_schema_extra') else {},
            ]}}
        }
    }
)
def read_purchases_route(
    skip: int = Query(0, ge=0, description="Registros a pular."),
    limit: int = Query(100, ge=1, le=100, description="Máximo de registros."),
    client_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID do cliente."),
    status: Optional[str] = Query(None, description="Filtrar por status (ex: pending)."),
    start_date: Optional[datetime] = Query(None, description="Data/hora inicial (ISO)."),
    end_date: Optional[datetime] = Query(None, description="Data/hora final (ISO)."),
    product_section_category_id: Optional[int] = Query(None, description="Filtrar por categoria de item."),
    product_section_gender_id: Optional[int] = Query(None, description="Filtrar por gênero de item."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna lista de pedidos com filtros. Requer auth.
    - **Regras de negócio**: Requer auth. Filtros opcionais. `client_id` (se cliente) só vê seus pedidos.
    - **Casos de uso**: Painel admin. Histórico de cliente. Relatórios.
    """
    return services.get_purchases(
        db, skip=skip, limit=limit, client_id=client_id, status=status,
        start_date=start_date, end_date=end_date,
        product_section_category_id=product_section_category_id,
        product_section_gender_id=product_section_gender_id
    )

@router.get(
    "/read/{purchase_id}",
    response_model=schemas.PurchaseResponse,
    summary="Busca um pedido específico por ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Pedido encontrado.",
            "content": {"application/json": {"example": schemas.PurchaseResponse.model_config['json_schema_extra']['example'] if schemas.PurchaseResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Pedido não encontrado"}}}}
    }
)
def read_purchase_route(
    purchase_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna detalhes de pedido específico, incluindo itens.
    - **Regras de negócio**: Pedido deve existir. Requer auth (cliente só vê seus pedidos).
    - **Casos de uso**: Detalhes de pedido. Cliente acompanhando status.
    """
    db_purchase = services.get_purchase(db, purchase_id)
    if db_purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return db_purchase

@router.put(
    "/update/{purchase_id}",
    response_model=schemas.PurchaseResponse,
    summary="Atualiza o status de um pedido.",
    responses={
        status.HTTP_200_OK: {
            "description": "Pedido atualizado.",
            "content": {"application/json": {"example": {**(schemas.PurchaseResponse.model_config.get('json_schema_extra', {}).get('example', {})), "status": "shipped"}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Pedido não encontrado"}}}}
    }
)
def update_purchase_route(
    purchase_id: uuid.UUID,
    purchase_data: schemas.PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza info de pedido (primariamente status).
    - **Regras de negócio**: Pedido deve existir. Apenas campos permitidos. Requer auth (admin/gerente). (Considerar transição de status).
    - **Casos de uso**: Marcar como 'pago', 'enviado'. Atualizar no painel admin.
    """
    db_purchase = services.update_purchase(db, purchase_id, purchase_data)
    if db_purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return db_purchase

@router.delete(
    "/delete/{purchase_id}",
    response_model=PurchaseMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Exclui um pedido (requer admin).",
    responses={
        status.HTTP_200_OK: {
            "description": "Pedido excluído. Estoque devolvido.",
            "content": {"application/json": {"example": PurchaseMessageResponse.model_config.get('json_schema_extra', {}).get('example', {"message": "Pedido deletado."}) }}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Pedido não encontrado"}}}},
        status.HTTP_403_FORBIDDEN: {"content": {"application/json": {"example": {"detail": "Acesso negado. Requer privilégios de administrador."}}}}
    }
)
def delete_purchase_route(
    purchase_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Exclui pedido. Estoque dos itens é devolvido. Requer admin.
    - **Regras de negócio**: Pedido deve existir. Apenas admins. Estoque retornado. (Considerar não excluir pedidos concluídos).
    - **Casos de uso**: Admin removendo pedido errado/fraudulento.
    """
    success = services.delete_purchase(db, purchase_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")
    return {"message": f"Pedido com ID {purchase_id} deletado com sucesso."}