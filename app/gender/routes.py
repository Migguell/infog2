from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from app.database.connection import get_db
from app.gender import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.gender.schemas import MessageResponse as GenderMessageResponse

router = APIRouter(
    prefix="/genders",
    tags=["Genders"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida ou nome de gênero já existente."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado."},
        status.HTTP_404_NOT_FOUND: {"description": "Gênero não encontrado."},
    }
)

@router.post(
    "/create",
    response_model=schemas.GenderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo gênero para produtos.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Gênero criado com sucesso.",
            "content": {"application/json": {"example": schemas.GenderResponse.model_config['json_schema_extra']['example'] if schemas.GenderResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_400_BAD_REQUEST: {"content": {"application/json": {"example": {"detail": "Gênero com este nome já existe."}}}}
    }
)
def create_gender_route(
    gender_data: schemas.GenderCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Cria novo gênero (Masculino, Feminino, etc.) para produtos.
    - **Regras de negócio**:
        - Nome curto (`name`) deve ser único. Requer auth.
    - **Casos de uso**:
        - Cadastrar "Masculino", "Infantil".
    """
    return services.create_gender(db, gender_data)

@router.get(
    "/read",
    response_model=List[schemas.GenderResponse],
    summary="Lista todos os gêneros cadastrados.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de gêneros retornada.",
            "content": {"application/json": {"example": [
                schemas.GenderResponse.model_config['json_schema_extra']['example'] if schemas.GenderResponse.model_config.get('json_schema_extra') else {},
                {"id": 2, "name": "F", "long_name": "Feminino", "created_at": "2024-05-25T10:01:00Z", "updated_at": "2024-05-25T10:01:00Z"}
            ]}}
        }
    }
)
def read_genders_route(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna lista de gêneros cadastrados, com paginação.
    - **Regras de negócio**: Requer auth.
    - **Casos de uso**:
        - Preencher seleção de gênero em formulário. Listar em painel admin.
    """
    return services.get_genders(db, skip=skip, limit=limit)

@router.get(
    "/read/{gender_id}",
    response_model=schemas.GenderResponse,
    summary="Busca um gênero específico por ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Gênero encontrado.",
            "content": {"application/json": {"example": schemas.GenderResponse.model_config['json_schema_extra']['example'] if schemas.GenderResponse.model_config.get('json_schema_extra') else {}}}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Gênero não encontrado"}}}}
    }
)
def read_gender_route(
    gender_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna detalhes de gênero específico pelo ID.
    - **Regras de negócio**: Gênero deve existir. Requer auth.
    - **Casos de uso**: Exibir detalhes ao editar produto.
    """
    db_gender = services.get_gender(db, gender_id)
    if db_gender is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gênero não encontrado")
    return db_gender

@router.put(
    "/update/{gender_id}",
    response_model=schemas.GenderResponse,
    summary="Atualiza um gênero existente.",
    responses={
        status.HTTP_200_OK: {
            "description": "Gênero atualizado.",
            "content": {"application/json": {"example": {**(schemas.GenderResponse.model_config.get('json_schema_extra', {}).get('example', {})), "long_name": "Masculino Adulto"}}}
        },
        status.HTTP_400_BAD_REQUEST: {"content": {"application/json": {"example": {"detail": "Novo nome de gênero já existe."}}}},
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Gênero não encontrado"}}}}
    }
)
def update_gender_route(
    gender_id: int,
    gender_data: schemas.GenderUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza dados de gênero existente.
    - **Regras de negócio**:
        - Gênero deve existir. `name` (se alterado) deve ser único. Requer auth.
    - **Casos de uso**: Corrigir nome. Alterar nome longo.
    """
    db_gender = services.update_gender(db, gender_id, gender_data)
    if db_gender is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gênero não encontrado")
    return db_gender

@router.delete(
    "/delete/{gender_id}",
    response_model=GenderMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Exclui um gênero (requer admin).",
    responses={
        status.HTTP_200_OK: {
            "description": "Gênero excluído.",
            "content": {"application/json": {"example": GenderMessageResponse.model_config.get('json_schema_extra', {}).get('example', {"message": "Gênero deletado com sucesso."}) }}
        },
        status.HTTP_404_NOT_FOUND: {"content": {"application/json": {"example": {"detail": "Gênero não encontrado"}}}},
        status.HTTP_403_FORBIDDEN: {"content": {"application/json": {"example": {"detail": "Acesso negado. Requer privilégios de administrador."}}}}
    }
)
def delete_gender_route(
    gender_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Exclui gênero. Requer admin.
    - **Regras de negócio**: Gênero deve existir. Apenas admins. (Considerar produtos vinculados).
    - **Casos de uso**: Admin removendo gênero não utilizado.
    """
    success = services.delete_gender(db, gender_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gênero não encontrado")
    return {"message": f"Gênero com ID {gender_id} deletado com sucesso."}