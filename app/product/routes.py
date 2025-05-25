from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid

from app.database.connection import get_db
from app.product import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.product.schemas import MessageResponse as ProductMessageResponse

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida, nome de produto já existente ou erro de validação."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado."},
        status.HTTP_404_NOT_FOUND: {"description": "Produto, ou recursos relacionados (imagens, categoria, etc.) não encontrados."},
    }
)

@router.post(
    "/create",
    response_model=schemas.ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo produto.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Produto criado com sucesso.",
            "content": {"application/json": {"example": schemas.ProductResponse.model_config['json_schema_extra']['example']}}
        },
        status.HTTP_400_BAD_REQUEST: {
            "content": {"application/json": {"example": {"detail": "Produto com este nome já existe."}}}
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Algumas imagens com IDs fornecidos não foram encontradas: [ids]"}}}
        }
    }
)
def create_product_route(
    product_data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Cria um novo produto no catálogo.

    Permite especificar nome, descrição, preço, estoque, e associar a tamanho, categoria, gênero
    e uma lista de IDs de imagens de produto já existentes.

    - **Regras de negócio**:
        - Nome do produto deve ser único.
        - `size_id`, `category_id`, `gender_id` devem referenciar registros existentes. (Validação FK no DB).
        - `product_image_ids` (se fornecido) deve conter IDs de `ProductImage` existentes. O serviço valida isso.
        - Requer autenticação de usuário.

    - **Casos de uso**:
        - Cadastrar um novo item de vestuário na loja.
        - Adicionar um novo produto com suas fotos já previamente cadastradas.
    """
    return services.create_product(db, product_data)

@router.get(
    "/read",
    response_model=List[schemas.ProductResponse],
    summary="Lista produtos com filtros e paginação.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de produtos retornada.",
            "content": {"application/json": {"example": [
                schemas.ProductResponse.model_config['json_schema_extra']['example'],
                {**schemas.ProductResponse.model_config['json_schema_extra']['example'], "id": "b2c3d4e5-f6a7-8901-2345-678901bcdef0", "name": "Calça Jeans Slim"}
            ]}}
        }
    }
)
def read_products_route(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=100, description="Máximo de registros a retornar."),
    category_id: Optional[int] = Query(None, description="Filtrar por ID da categoria."),
    gender_id: Optional[int] = Query(None, description="Filtrar por ID do gênero."),
    min_price: Optional[float] = Query(None, description="Filtrar por preço mínimo."),
    max_price: Optional[float] = Query(None, description="Filtrar por preço máximo."),
    available_only: bool = Query(False, description="Mostrar apenas produtos com estoque > 0."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna uma lista de produtos, com opções de filtro e paginação.

    Permite filtrar por categoria, gênero, faixa de preço e disponibilidade em estoque.

    - **Regras de negócio**:
        - Requer autenticação de usuário.
        - Todos os filtros são opcionais.

    - **Casos de uso**:
        - Exibir catálogo de produtos em uma loja virtual com filtros.
        - Painel administrativo para buscar e gerenciar produtos.
        - API para aplicativo móvel listando produtos por critérios.
    """
    return services.get_products(
        db, skip=skip, limit=limit, category_id=category_id,
        gender_id=gender_id, min_price=min_price,
        max_price=max_price, available_only=available_only
    )

@router.get(
    "/read/{product_id}",
    response_model=schemas.ProductResponse,
    summary="Busca um produto específico por ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Produto encontrado.",
            "content": {"application/json": {"example": schemas.ProductResponse.model_config['json_schema_extra']['example']}}
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Produto não encontrado"}}}
        }
    }
)
def read_product_route(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna os detalhes de um produto específico, incluindo suas imagens associadas.

    - **Regras de negócio**:
        - O produto deve existir.
        - Requer autenticação de usuário.

    - **Casos de uso**:
        - Exibir a página de detalhes de um produto em um e-commerce.
        - Carregar dados de um produto para edição em um painel administrativo.
    """
    db_product = services.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return db_product

@router.put(
    "/update/{product_id}",
    response_model=schemas.ProductResponse,
    summary="Atualiza um produto existente.",
    responses={
        status.HTTP_200_OK: {
            "description": "Produto atualizado com sucesso.",
            "content": {"application/json": {"example": {**schemas.ProductResponse.model_config['json_schema_extra']['example'], "price": "139.90"}}}
        },
        status.HTTP_400_BAD_REQUEST: {
            "content": {"application/json": {"example": {"detail": "Novo nome de produto já existe."}}}
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Produto não encontrado ou imagem associada não encontrada."}}}
        }
    }
)
def update_product_route(
    product_id: uuid.UUID,
    product_data: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza os dados de um produto existente.

    Permite alterar qualquer campo do produto, incluindo a lista de IDs de imagens associadas.
    A lógica de atualização de imagens no serviço pode desassociar/remover imagens não presentes na nova lista `product_image_ids`.

    - **Regras de negócio**:
        - O produto deve existir.
        - Novo nome (se fornecido) deve ser único.
        - IDs em `product_image_ids` (se fornecido) devem corresponder a imagens existentes.
        - Requer autenticação de usuário.

    - **Casos de uso**:
        - Editar informações de um produto no painel de controle.
        - Alterar o preço ou estoque de um item.
        - Reorganizar ou trocar as imagens de um produto.
    """
    db_product = services.update_product(db, product_id, product_data)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return db_product

@router.delete(
    "/delete/{product_id}",
    response_model=ProductMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Exclui um produto (requer admin).",
    responses={
        status.HTTP_200_OK: {
            "description": "Produto excluído com sucesso.",
            "content": {"application/json": {"example": {"message": f"Produto com ID {uuid.uuid4()} deletado com sucesso."}}}
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Produto não encontrado"}}}
        },
        status.HTTP_403_FORBIDDEN: {
            "content": {"application/json": {"example": {"detail": "Acesso negado. Requer privilégios de administrador."}}}
        }
    }
)
def delete_product_route(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Exclui um produto do sistema, incluindo suas imagens associadas.

    **Atenção**: Requer privilégios de administrador. Esta operação é destrutiva.
    O serviço também deleta as `ProductImage` associadas.

    - **Regras de negócio**:
        - O produto deve existir.
        - Apenas usuários administradores podem excluir produtos.
        - (Consideração) Verificar se o produto está em pedidos abertos antes da exclusão.

    - **Casos de uso**:
        - Remover um produto descontinuado do catálogo.
        - Limpeza de dados por um administrador.
    """
    success = services.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return {"message": f"Produto com ID {product_id} deletado com sucesso."}