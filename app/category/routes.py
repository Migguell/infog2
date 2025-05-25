from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Annotated

from app.database.connection import get_db
from app.category import schemas, services
from app.database import models
from app.category.schemas import MessageResponse as CategoryMessageResponse
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/categories",
    tags=["Category"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida ou nome de categoria já existente."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado (necessário token válido)."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado (ex: rota de deleção apenas para admin)."},
        status.HTTP_404_NOT_FOUND: {"description": "Categoria não encontrada."},
    }
)

@router.post(
    "/create",
    response_model=schemas.CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova categoria de produtos",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Categoria criada com sucesso.",
            "content": {
                "application/json": {
                    "schema": schemas.CategoryResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.CategoryResponse.model_config['json_schema_extra']['example'] if schemas.CategoryResponse.model_config.get('json_schema_extra') else {}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {"description": "Nome da categoria já existe ou dados inválidos.", "content": {"application/json": {"example": {"detail": "Categoria com este nome já existe."}}}},
    }
)
def create_category_route(
    category_data: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Cria uma nova categoria para agrupar produtos.
    - **Regras de negócio**:
        - O nome da categoria deve ser único e ter entre 1 e 50 caracteres.
        - Apenas usuários autenticados podem criar categorias.
    - **Casos de uso**:
        - Administrador adicionando nova linha de produtos.
        - Organização de produtos para e-commerce.
    """
    db_category = services.create_category(db, category_data)
    return db_category

@router.get(
    "/read",
    response_model=List[schemas.CategoryResponse],
    summary="Lista todas as categorias de produtos",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de categorias retornada com sucesso.",
            "content": {
                "application/json": {
                    "schema": {"type": "array", "items": schemas.CategoryResponse.model_json_schema(ref_template="#/components/schemas/{model}")},
                    "example": [
                        schemas.CategoryResponse.model_config['json_schema_extra']['example'] if schemas.CategoryResponse.model_config.get('json_schema_extra') else {},
                        {"id": 2, "name": "Calçados", "created_at": "2024-05-23T10:00:00Z", "updated_at": "2024-05-23T10:00:00Z"}
                    ]
                }
            }
        }
    }
)
def read_categories_route(
    skip: int = Query(0, ge=0, description="Número de registros a pular para paginação."),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a retornar."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna lista de categorias cadastradas, com paginação.
    - **Regras de negócio**:
        - Apenas usuários autenticados. `skip` >= 0, `limit` entre 1 e 100.
    - **Casos de uso**:
        - Exibir filtros de categoria. Painel administrativo.
    """
    categories = services.get_categories(db, skip=skip, limit=limit)
    return categories

@router.get(
    "/read/{category_id}",
    response_model=schemas.CategoryResponse,
    summary="Busca uma categoria específica por ID",
    responses={
        status.HTTP_200_OK: {
            "description": "Categoria encontrada e retornada.",
            "content": {
                "application/json": {
                    "schema": schemas.CategoryResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.CategoryResponse.model_config['json_schema_extra']['example'] if schemas.CategoryResponse.model_config.get('json_schema_extra') else {}
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {"description": "Categoria não encontrada.", "content": {"application/json": {"example": {"detail": "Categoria não encontrada"}}}},
    }
)
def read_category_route(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna detalhes de uma categoria específica pelo ID.
    - **Regras de negócio**:
        - Categoria deve existir. Apenas usuários autenticados.
    - **Casos de uso**:
        - Detalhes em painel admin. Carregar info ao selecionar filtro.
    """
    db_category = services.get_category(db, category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return db_category

@router.put(
    "/update/{category_id}",
    response_model=schemas.CategoryResponse,
    summary="Atualiza uma categoria existente",
    responses={
        status.HTTP_200_OK: {
            "description": "Categoria atualizada com sucesso.",
            "content": {
                "application/json": {
                    "schema": schemas.CategoryResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": {**(schemas.CategoryResponse.model_config.get('json_schema_extra', {}).get('example', {})), "name": "Camisetas Atualizadas"}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {"description": "Novo nome já existe ou inválido.", "content": {"application/json": {"example": {"detail": "Novo nome de categoria já existe."}}}},
        status.HTTP_404_NOT_FOUND: {"description": "Categoria não encontrada.", "content": {"application/json": {"example": {"detail": "Categoria não encontrada"}}}},
    }
)
def update_category_route(
    category_id: int,
    category_data: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza o nome de uma categoria.
    - **Regras de negócio**:
        - Categoria deve existir. Novo nome (se fornecido) deve ser único e ter entre 1-50 chars.
        - Apenas usuários autenticados.
    - **Casos de uso**:
        - Corrigir nome de categoria. Renomear categoria.
    """
    db_category = services.update_category(db, category_id, category_data)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return db_category

@router.delete(
    "/delete/{category_id}",
    response_model=CategoryMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Deleta uma categoria",
    responses={
        status.HTTP_200_OK: {
            "description": "Categoria deletada com sucesso.",
            "content": {
                "application/json": {
                    "schema": CategoryMessageResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": CategoryMessageResponse.model_config.get('json_schema_extra', {}).get('example', {"message": "Categoria deletada com sucesso."})
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {"description": "Categoria não encontrada.", "content": {"application/json": {"example": {"detail": "Categoria não encontrada"}}}},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado. Requer admin.", "content": {"application/json": {"example": {"detail": "Acesso negado. Requer privilégios de administrador."}}}},
    }
)
def delete_category_route(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Deleta uma categoria. Requer privilégios de administrador.
    - **Regras de negócio**:
        - Categoria deve existir. Apenas admins.
        - (Considerar) Impedir exclusão se produtos vinculados.
    - **Casos de uso**:
        - Remover categoria obsoleta.
    """
    success = services.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return {"message": f"Categoria com ID {category_id} deletada com sucesso."}