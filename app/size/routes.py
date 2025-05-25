from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from app.database.connection import get_db
from app.size import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.size.schemas import MessageResponse as SizeMessageResponse

router = APIRouter(
    prefix="/sizes",
    tags=["Tamanhos"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida ou nome de tamanho já existente."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado."},
        status.HTTP_404_NOT_FOUND: {"description": "Tamanho não encontrado."},
    }
)

@router.post(
    "/create",
    response_model=schemas.SizeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo tamanho para produtos.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Tamanho criado com sucesso.",
            "content": {"application/json": {"example": schemas.SizeResponse.model_config['json_schema_extra']['example'] if schemas.SizeResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_400_BAD_REQUEST: {"content": {"application/json": {"example": {"detail": "Tamanho com este nome já existe."}}}}
    }
)
def create_size_route(
    size_data: schemas.SizeCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Cria novo tamanho (P, M, G) para produtos.
    - **Regras de negócio**: `name` deve ser único. Requer auth.
    - **Casos de uso**: Cadastrar "P", "38".
    """
    return services.create_size(db, size_data)

@router.get(
    "/read",
    response_model=List[schemas.SizeResponse],
    summary="Lista todos os tamanhos cadastrados.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de tamanhos retornada.",
            "content": {"application/json": {"example": [
                schemas.SizeResponse.model_config['json_schema_extra']['example'] if schemas.SizeResponse.model_config.get('json_schema_extra') else {},
                {"id": 2, "name": "G", "long_name": "Grande", "created_at": "2024-05-25T09:01:00Z", "updated_at": "2024-05-25T09:01:00Z"}
            ]}}
        }
    }
)
def read_sizes_route(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna lista de tamanhos cadastrados, com paginação.
    - **Regras de negócio**: Requer auth.
    - **Casos de uso**: Preencher seleção de tamanho. Listar em painel admin. Filtro de cliente.
    """
    return services.get_sizes(db, skip=skip, limit=limit)

@router.get(
    "/read/{size_id}",
    response_model=schemas.SizeResponse,
    summary="Busca um tamanho específico por ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Tamanho encontrado.",
            "content": {"application/json": {"example": schemas.SizeResponse.model_config['json_schema_extra']['example'] if schemas.SizeResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Tamanho não encontrado"}}}}
    }
)
def read_size_route(
    size_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna detalhes de tamanho específico pelo ID.
    - **Regras de negócio**: Tamanho deve existir. Requer auth.
    - **Casos de uso**: Exibir detalhes ao editar produto.
    """
    db_size = services.get_size(db, size_id)
    if db_size is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tamanho não encontrado")
    return db_size

@router.put(
    "/update/{size_id}",
    response_model=schemas.SizeResponse,
    summary="Atualiza um tamanho existente.",
    responses={
        status.HTTP_200_OK: {
            "description": "Tamanho atualizado.",
            "content": {"application/json": {"example": {**(schemas.SizeResponse.model_config.get('json_schema_extra', {}).get('example', {})), "long_name": "Médio (M)"}}}
        },
        status.HTTP_400_BAD_REQUEST: {"content": {"application/json": {"example": {"detail": "Novo nome de tamanho já existe."}}}},
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Tamanho não encontrado"}}}}
    }
)
def update_size_route(
    size_id: int,
    size_data: schemas.SizeUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza dados de tamanho (nome curto, nome longo).
    - **Regras de negócio**: Tamanho deve existir. `name` (se alterado) único. Requer auth.
    - **Casos de uso**: Corrigir nome. Alterar nome longo.
    """
    db_size = services.update_size(db, size_id, size_data)
    if db_size is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tamanho não encontrado")
    return db_size

@router.delete(
    "/delete/{size_id}",
    response_model=SizeMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Exclui um tamanho (requer admin).",
    responses={
        status.HTTP_200_OK: {
            "description": "Tamanho excluído.",
            "content": {"application/json": {"example": SizeMessageResponse.model_config.get('json_schema_extra', {}).get('example', {"message": "Tamanho deletado."})}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Tamanho não encontrado"}}}},
        status.HTTP_403_FORBIDDEN: {"content": {"application/json": {"example": {"detail": "Acesso negado. Requer privilégios de administrador."}}}}
    }
)
def delete_size_route(
    size_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Exclui tamanho. Requer admin.
    - **Regras de negócio**: Tamanho deve existir. Apenas admins. (Considerar produtos/pedidos vinculados).
    - **Casos de uso**: Admin removendo tamanho não utilizado.
    """
    success = services.delete_size(db, size_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tamanho não encontrado")
    return {"message": f"Tamanho com ID {size_id} deletado com sucesso."}