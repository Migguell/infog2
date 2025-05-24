from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.connection import get_db
from app.auth import schemas, services
from app.database import models
from app.core.dependencies import get_current_active_user, create_token_response

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Requisição inválida"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado"},
        status.HTTP_403_FORBIDDEN: {"description": "Acesso negado"},
        status.HTTP_404_NOT_FOUND: {"description": "Recurso não encontrado"},
    }
)

@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo usuário",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Usuário registrado com sucesso.",
            "content": {
                "application/json": {
                    "schema": schemas.UserResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.UserResponse.model_config['json_schema_extra']['example'] if schemas.UserResponse.model_config.get('json_schema_extra') else {}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Erro de validação ou email/CPF já registrado.",
            "content": {
                "application/json": {
                    "examples": {
                        "email_exists": {"summary": "Email já registrado", "value": {"detail": "Email já registrado."}},
                        "cpf_exists": {"summary": "CPF já registrado", "value": {"detail": "CPF já registrado."}},
                        "validation_error": {"summary": "Erro de validação", "value": {"detail": [{"loc": ["body", "cpf"], "msg": "value is not a valid string", "type": "string_type"}]}}
                    }
                }
            }
        }
    }
)
def register_user_route(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário (não administrador) no sistema.
    Este endpoint permite que novos usuários se cadastrem fornecendo nome, CPF, email e senha.
    - **Regras de negócio**:
        - O CPF deve ser único e conter exatamente 11 dígitos.
        - O email deve ser único e válido.
        - A senha deve ter no mínimo 6 caracteres.
        - Após o registro, o usuário é marcado como ativo.
        - Novos usuários registrados por este endpoint não são administradores por padrão.
    - **Casos de uso**:
        - Novos clientes se cadastrando na plataforma pela primeira vez.
        - Formulário de "Criar Conta" em um site ou aplicativo móvel.
    """
    db_user = services.register_user(db, user_data)
    return db_user

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Realiza login do usuário",
    responses={
        status.HTTP_200_OK: {
            "description": "Login bem-sucedido, token de acesso retornado.",
            "content": {
                "application/json": {
                    "schema": schemas.Token.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.Token.model_config['json_schema_extra']['example'] if schemas.Token.model_config.get('json_schema_extra') else {}
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Credenciais inválidas (email ou senha incorretos).",
            "content": {"application/json": {"example": {"detail": "Credenciais inválidas"}}},
            "headers": {"WWW-Authenticate": {"schema": {"type": "string"}, "example": "Bearer"}}
        }
    }
)
def login_for_access_token(
    user_login: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """
    Autentica um usuário existente e retorna um token de acesso JWT.
    O usuário fornece email e senha para autenticação. Se as credenciais forem válidas, um token JWT é gerado.
    - **Regras de negócio**:
        - O usuário deve estar previamente registrado e ativo.
        - O email e a senha fornecidos devem corresponder a um registro no banco de dados.
        - O token gerado tem um tempo de expiração definido.
    - **Casos de uso**:
        - Usuário fazendo login em um sistema web ou mobile.
        - Obtenção de token para chamadas API subsequentes.
    """
    user = services.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas", headers={"WWW-Authenticate": "Bearer"})
    return create_token_response(subject_id=user.id, is_admin=user.is_admin)

@router.post(
    "/refresh-token",
    response_model=schemas.Token,
    summary="Atualiza o token de acesso",
    responses={
        status.HTTP_200_OK: {
            "description": "Novo token de acesso gerado com sucesso.",
            "content": {
                "application/json": {
                    "schema": schemas.Token.model_json_schema(ref_template="#/components/schemas/{model}"),
                    "example": schemas.Token.model_config['json_schema_extra']['example'] if schemas.Token.model_config.get('json_schema_extra') else {}
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token inválido, expirado ou usuário inativo.",
            "content": {
                "application/json": {
                    "examples": {
                        "not_validated": {"summary": "Credenciais não validadas", "value": {"detail": "Não foi possível validar as credenciais"}},
                        "inactive_user": {"summary": "Usuário inativo", "value": {"detail": "Usuário inativo"}}
                    }
                }
            },
             "headers": {"WWW-Authenticate": {"schema": {"type": "string"}, "example": "Bearer"}}
        }
    }
)
def refresh_access_token(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    Gera um novo token de acesso JWT para um usuário autenticado.
    Requer um token de acesso válido no cabeçalho de autorização.
    - **Regras de negócio**:
        - Um token de acesso JWT válido e ativo deve ser fornecido.
        - O usuário associado ao token deve estar ativo.
    - **Casos de uso**:
        - Aplicações cliente renovando tokens para manter sessão.
    """
    return create_token_response(subject_id=current_user.id, is_admin=current_user.is_admin)