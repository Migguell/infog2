from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import models

def test_register_user_success(client: TestClient, db_session: Session):
    """
    Testa o registro bem-sucedido de um novo usuário.
    """
    user_data = {
        "name": "Teste Usuario Sucesso",
        "cpf": "01234567890",
        "email": "sucesso@example.com",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 201, f"Status code inesperado: {response.json()}"
    response_data = response.json()

    assert response_data["name"] == user_data["name"]
    assert response_data["email"] == user_data["email"]
    assert response_data["cpf"] == user_data["cpf"]
    assert "id" in response_data
    assert response_data["is_active"] is True
    assert response_data["is_admin"] is False

    db_user = db_session.query(models.User).filter(models.User.email == user_data["email"]).first()
    assert db_user is not None
    assert db_user.name == user_data["name"]


def test_register_user_duplicate_email(client: TestClient, db_session: Session):
    """
    Testa a tentativa de registrar um usuário com um email que já existe.
    """
    initial_user_data = {
        "name": "Usuario Existente Email Test",
        "cpf": "11122233301",
        "email": "duplicado.email.test@example.com",
        "password": "password123"
    }
    client.post("/auth/register", json=initial_user_data)

    duplicate_user_data = {
        "name": "Outro Usuario",
        "cpf": "11122233302",
        "email": "duplicado.email.test@example.com",
        "password": "password456"
    }
    response_duplicate = client.post("/auth/register", json=duplicate_user_data)

    assert response_duplicate.status_code == 400
    assert "Email já registrado" in response_duplicate.json()["detail"]


def test_register_user_duplicate_cpf(client: TestClient, db_session: Session):
    """
    Testa a tentativa de registrar um usuário com um CPF que já existe.
    """
    initial_user_data = {
        "name": "Usuario Existente CPF Test",
        "cpf": "22233344401",
        "email": "unico.cpf.test@example.com",
        "password": "password123"
    }
    client.post("/auth/register", json=initial_user_data)

    duplicate_user_data = {
        "name": "Mais Um Usuario",
        "cpf": "22233344401",
        "email": "outro.email.unico.test@example.com",
        "password": "password789"
    }
    response_duplicate = client.post("/auth/register", json=duplicate_user_data)

    assert response_duplicate.status_code == 400
    assert "CPF já registrado" in response_duplicate.json()["detail"]


def test_register_user_invalid_data_short_password(client: TestClient):
    """
    Testa o registro com senha muito curta.
    """
    user_data = {
        "name": "Senha Curta Test",
        "cpf": "33344455500",
        "email": "senhacurta.test@example.com",
        "password": "123"
    }
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 422
    response_data = response.json()
    assert any(err["loc"] == ["body", "password"] for err in response_data["detail"])
    assert any("String should have at least 6 characters" in err["msg"] for err in response_data["detail"])


def test_register_user_invalid_data_invalid_cpf(client: TestClient):
    """
    Testa o registro com CPF inválido (curto demais).
    Seu schema UserCreate tem min_length=11 e max_length=11 para CPF.
    """
    user_data = {
        "name": "CPF Curto Test",
        "cpf": "12345",
        "email": "cpfcurto.test@example.com",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 422
    response_data = response.json()
    assert any(err["loc"] == ["body", "cpf"] for err in response_data["detail"])
    assert any("String should have at least 11 characters" in err["msg"] for err in response_data["detail"])


def test_register_user_invalid_data_invalid_email(client: TestClient):
    """
    Testa o registro com email inválido.
    """
    user_data = {
        "name": "Email Invalido Test",
        "cpf": "44455566600",
        "email": "emailinvalido",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 422
    response_data = response.json()
    assert any(err["loc"] == ["body", "email"] for err in response_data["detail"])
    assert any("valid email address" in err["msg"] for err in response_data["detail"])