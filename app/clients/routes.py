from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
import uuid

from app.database.connection import get_db
from app.clients import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, get_current_admin_user, create_token_response
from app.clients.schemas import MessageResponse as ClientMessageResponse

router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida, dados duplicados (email/CPF) ou erro de validação."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado (necessário token de usuário/admin)."},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado (ex: deleção apenas para admin)."},
        status.HTTP_404_NOT_FOUND: {"description": "Cliente não encontrado."},
    }
)

@router.post(
    "/create",
    response_model=schemas.ClientCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo cliente e retorna dados do cliente com token de acesso.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Cliente criado com sucesso. Retorna os dados do cliente e um token de acesso para ele.",
            "content": {
                "application/json": {
                    "schema": schemas.ClientCreateResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.ClientCreateResponse.model_config['json_schema_extra']['example'] if schemas.ClientCreateResponse.model_config.get('json_schema_extra') else {}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Erro de validação, ou email/CPF já registrado.",
            "content": {"application/json": {"examples": {"email_exists": {"summary": "Email duplicado", "value": {"detail": "Email já registrado."}},"cpf_exists": {"summary": "CPF duplicado", "value": {"detail": "CPF já registrado."}}}}}
        }
    }
)
def create_client_route(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo cliente no sistema. Não requer autenticação prévia.
    Retorna dados do cliente e token JWT para autenticação subsequente como cliente.
    - **Regras de negócio**:
        - CPF único, 11 dígitos. Email único e válido. Senha >= 6 chars.
        - Token de acesso específico para cliente é gerado.
    - **Casos de uso**:
        - Novo cliente se cadastrando. Formulário "Cadastre-se".
    """
    db_client = services.create_client(db, client_data)
    client_response_data = {"id": db_client.id, "name": db_client.name, "email": db_client.email, "cpf": db_client.cpf, "created_at": db_client.created_at, "updated_at": db_client.updated_at}
    return schemas.ClientCreateResponse(client=schemas.ClientResponse(**client_response_data), token=create_token_response(subject_id=db_client.id, is_client=True))

@router.get(
    "/read",
    response_model=List[schemas.ClientResponse],
    summary="Lista todos os clientes cadastrados (requer autenticação de usuário).",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de clientes retornada com sucesso.",
            "content": {
                "application/json": {
                    "schema": {"type": "array", "items": schemas.ClientResponse.model_json_schema(ref_template="#/components/schemas/{model}")},
                    "example": [
                        schemas.ClientResponse.model_config['json_schema_extra']['example'] if schemas.ClientResponse.model_config.get('json_schema_extra') else {},
                        {**(schemas.ClientResponse.model_config.get('json_schema_extra', {}).get('example', {})), "id": "d290f1ee-6c54-4b01-90e6-d701748f0851", "name": "Carlos Pereira", "email": "carlos.pereira@example.com", "cpf":"11223344556"}
                    ]
                }
            }
        }
    }
)
def read_clients_route(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros."),
    name: Optional[str] = Query(None, description="Filtrar por nome (case-insensitive, parcial)."),
    email: Optional[str] = Query(None, description="Filtrar por email (case-insensitive, parcial)."),
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna lista de clientes, com paginação e filtros. Requer auth de usuário (não cliente).
    - **Regras de negócio**:
        - Apenas usuários autenticados (não clientes). Filtros opcionais.
    - **Casos de uso**:
        - Admin visualizando clientes. CRM. Suporte ao cliente.
    """
    clients = services.get_clients(db, skip=skip, limit=limit, name=name, email=email)
    return clients

@router.get(
    "/read/{client_id}",
    response_model=schemas.ClientResponse,
    summary="Busca um cliente específico por ID (requer autenticação de usuário).",
    responses={
        status.HTTP_200_OK: {
            "description": "Cliente encontrado e retornado.",
            "content": {
                "application/json": {
                    "schema": schemas.ClientResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.ClientResponse.model_config['json_schema_extra']['example'] if schemas.ClientResponse.model_config.get('json_schema_extra') else {}
                }
            }
        }
    }
)
def read_client_route(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Retorna detalhes de um cliente pelo ID. Requer auth de usuário (não cliente).
    - **Regras de negócio**:
        - Cliente deve existir. Apenas usuários autenticados (não clientes).
    - **Casos de uso**:
        - Detalhes em painel admin. Carregar perfil para atendimento.
    """
    db_client = services.get_client(db, client_id)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return db_client

@router.put(
    "/update/{client_id}",
    response_model=schemas.ClientResponse,
    summary="Atualiza dados de um cliente (requer autenticação de usuário).",
    responses={
        status.HTTP_200_OK: {
            "description": "Cliente atualizado com sucesso.",
            "content": {
                "application/json": {
                    "schema": schemas.ClientResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": {**(schemas.ClientResponse.model_config.get('json_schema_extra', {}).get('example', {})), "name": "Maria Oliveira Souza"}
                }
            }
        }
    }
)
def update_client_route(
    client_id: uuid.UUID,
    client_data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_active_user)] = None
):
    """
    Atualiza dados de cliente. Requer auth de usuário (não cliente).
    - **Regras de negócio**:
        - Cliente deve existir. Email/CPF (se alterados) devem ser únicos. Senha (se alterada) >= 6 chars.
    - **Casos de uso**:
        - Admin corrigindo dados. Cliente atualizando perfil (com ajuste de permissão).
    """
    db_client = services.update_client(db, client_id, client_data)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return db_client

@router.delete(
    "/delete/{client_id}",
    response_model=ClientMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Exclui um cliente (requer autenticação de administrador).",
    responses={
        status.HTTP_200_OK: {
            "description": "Cliente excluído com sucesso.",
            "content": {
                "application/json": {
                    "schema": ClientMessageResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": ClientMessageResponse.model_config.get('json_schema_extra', {}).get('example', {"message": "Cliente deletado com sucesso."})
                }
            }
        }
    }
)
def delete_client_route(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[models.User, Depends(get_current_admin_user)] = None
):
    """
    Exclui cliente. Requer admin. Operação destrutiva.
    - **Regras de negócio**:
        - Cliente deve existir. Apenas admins.
        - (Considerar) Políticas de retenção/anonimização.
    - **Casos de uso**:
        - Admin removendo conta. LGPD (com ressalvas).
    """
    success = services.delete_client(db, client_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return {"message": f"Cliente com ID {client_id} deletado com sucesso."}