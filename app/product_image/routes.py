from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid

from app.database.connection import get_db
from app.product_image import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.product_image.schemas import MessageResponse as ProductImageMessageResponse

router = APIRouter(
    prefix="/product-images",
    tags=["Imagens de Produtos"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado."},
        status.HTTP_404_NOT_FOUND: {"description": "Imagem ou produto associado não encontrado."},
    }
)

@router.post(
    "/create",
    response_model=schemas.ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova imagem para um produto.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Imagem do produto criada com sucesso.",
            "content": {"application/json": {"example": schemas.ProductImageResponse.model_config['json_schema_extra']['example'] if schemas.ProductImageResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Produto associado não encontrado."}}}}
    }
)
def create_product_image_route(
    image_data: schemas.ProductImageCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Adiciona nova imagem e associa a produto existente.
    - **Regras de negócio**:
        - `product_id` deve existir. URL válida. Requer auth.
    - **Casos de uso**:
        - Adicionar múltiplas fotos a produto. Carregar imagem principal/secundárias.
    """
    return services.create_product_image(db, image_data)

@router.get(
    "/read",
    response_model=List[schemas.ProductImageResponse],
    summary="Lista imagens de produtos, com filtro opcional por ID do produto.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de imagens de produtos retornada.",
            "content": {"application/json": {"example": [
                schemas.ProductImageResponse.model_config['json_schema_extra']['example'] if schemas.ProductImageResponse.model_config.get('json_schema_extra') else {},
                {**(schemas.ProductImageResponse.model_config.get('json_schema_extra', {}).get('example', {})), "id": "eeddccbb-aa99-8877-6655-4433221100ff", "url": "http://example.com/images/produto_detalhe.jpg", "is_main": False}
            ]}}
        }
    }
)
def read_product_images_route(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros."),
    product_id: Optional[uuid.UUID] = Query(None, description="Filtrar imagens por ID do produto."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna lista de imagens de produtos. Pode filtrar por `product_id`.
    - **Regras de negócio**: Requer auth.
    - **Casos de uso**: Listar imagens de produto. Painel de mídia.
    """
    return services.get_product_images(db, skip=skip, limit=limit, product_id=product_id)

@router.get(
    "/read/{image_id}",
    response_model=schemas.ProductImageResponse,
    summary="Busca uma imagem de produto específica por ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Imagem do produto encontrada.",
            "content": {"application/json": {"example": schemas.ProductImageResponse.model_config['json_schema_extra']['example'] if schemas.ProductImageResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Imagem não encontrada"}}}}
    }
)
def read_product_image_route(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna detalhes de imagem de produto específica.
    - **Regras de negócio**: Imagem deve existir. Requer auth.
    - **Casos de uso**: Visualizar metadados de imagem.
    """
    db_image = services.get_product_image(db, image_id)
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")
    return db_image

@router.put(
    "/update/{image_id}",
    response_model=schemas.ProductImageResponse,
    summary="Atualiza uma imagem de produto existente.",
    responses={
        status.HTTP_200_OK: {
            "description": "Imagem do produto atualizada.",
            "content": {"application/json": {"example": {**(schemas.ProductImageResponse.model_config.get('json_schema_extra', {}).get('example', {})), "description": "Nova descrição."}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Imagem não encontrada"}}}}
    }
)
def update_product_image_route(
    image_id: uuid.UUID,
    image_data: schemas.ProductImageUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza dados de imagem (URL, descrição, is_main).
    - **Regras de negócio**: Imagem deve existir. Requer auth.
    - **Casos de uso**: Corrigir URL. Alterar descrição/status de principal.
    """
    db_image = services.update_product_image(db, image_id, image_data)
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")
    return db_image

@router.delete(
    "/delete/{image_id}",
    response_model=ProductImageMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Exclui uma imagem de produto (requer admin).",
    responses={
        status.HTTP_200_OK: {
            "description": "Imagem do produto excluída.",
            "content": {"application/json": {"example": ProductImageMessageResponse.model_config.get('json_schema_extra', {}).get('example', {"message": "Imagem deletada."})}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Imagem não encontrada"}}}},
        status.HTTP_403_FORBIDDEN: {"content": {"application/json": {"example": {"detail": "Acesso negado. Requer privilégios de administrador."}}}}
    }
)
def delete_product_image_route(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Exclui imagem de produto. Requer admin.
    - **Regras de negócio**: Imagem deve existir. Apenas admins. Desassocia do produto.
    - **Casos de uso**: Remover imagem desatualizada/incorreta.
    """
    success = services.delete_product_image(db, image_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")
    return {"message": f"Imagem com ID {image_id} deletada com sucesso."}