from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import uuid

from app.database import models
from app.auth.services import get_password_hash
from app.core.dependencies import create_token_response

VALID_TEST_PASSWORD = "testpassword123"

def get_gender_test_token(db_session: Session, is_admin: bool, unique_marker: str = "") -> str:
    """
    Cria um usuário de teste (models.User) na sessão atual para os testes de Gênero
    e retorna um token de acesso para ele. Não usa cache global.
    """
    email_base = f"gender_test_{'admin' if is_admin else 'user'}"
    email_suffix = uuid.uuid4().hex[:8]
    email = f"{email_base}_{unique_marker}_{email_suffix}@example.com"
    
    cpf_flag = 'G1' if is_admin else 'G2'
    cpf_hash_part = abs(hash(email)) % 10000000
    cpf = (cpf_flag + str(cpf_hash_part).zfill(9))[:11]

    test_user = models.User(
        name=f"Gender Test {'Admin' if is_admin else 'User'} {unique_marker} {email_suffix}",
        email=email,
        cpf=cpf, 
        hashed_password=get_password_hash(VALID_TEST_PASSWORD),
        is_active=True,
        is_admin=is_admin
    )
    db_session.add(test_user)
    try:
        db_session.commit()
        db_session.refresh(test_user)
    except Exception as e:
        db_session.rollback()
        raise 
            
    token_data = create_token_response(subject_id=test_user.id, is_admin=test_user.is_admin)
    return token_data.access_token


def test_create_gender_success(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="create_success")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    gender_name = f"Masc-{uuid.uuid4().hex[:6]}"
    gender_long_name = f"Masculino Teste {uuid.uuid4().hex[:6]}"
    gender_data = {"name": gender_name, "long_name": gender_long_name}
    
    response = client.post("/genders/create", json=gender_data, headers=headers)
    assert response.status_code == 201, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["name"] == gender_name
    assert data["long_name"] == gender_long_name
    assert "id" in data
    
    db_gender = db_session.query(models.Gender).filter(models.Gender.id == data["id"]).first()
    assert db_gender is not None
    assert db_gender.name == gender_name

def test_create_gender_duplicate_name(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="create_dup")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    gender_name = "UnisexDupTest"
    existing = db_session.query(models.Gender).filter(models.Gender.name == gender_name).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    gender_data = {"name": gender_name, "long_name": "Unissex para Teste de Duplicidade"}
    resp1 = client.post("/genders/create", json=gender_data, headers=headers)
    assert resp1.status_code == 201, f"Primeira criação falhou: {resp1.json()}"
    
    gender_data_dup = {"name": gender_name, "long_name": "Outra Descrição"}
    response = client.post("/genders/create", json=gender_data_dup, headers=headers) 
    assert response.status_code == 400
    assert "Gênero com este nome já existe" in response.json()["detail"]

def test_read_genders_list(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="read_list")
    headers = {"Authorization": f"Bearer {user_token}"}

    name1 = f"Fem-{uuid.uuid4().hex[:6]}"
    name2 = f"Kid-{uuid.uuid4().hex[:6]}"
    
    resp1 = client.post("/genders/create", json={"name": name1, "long_name": "Feminino Teste Lista"}, headers=headers)
    assert resp1.status_code == 201, f"Erro ao criar gênero {name1}: {resp1.json()}"
    resp2 = client.post("/genders/create", json={"name": name2, "long_name": "Infantil Teste Lista"}, headers=headers)
    assert resp2.status_code == 201, f"Erro ao criar gênero {name2}: {resp2.json()}"
    
    response = client.get("/genders/read", headers=headers)
    assert response.status_code == 200, f"Erro ao ler gêneros: {response.json()}"
    data = response.json()
    assert isinstance(data, list)
    
    names_in_response = [item["name"] for item in data]
    assert name1 in names_in_response, f"{name1} não encontrado em {names_in_response}"
    assert name2 in names_in_response, f"{name2} não encontrado em {names_in_response}"

def test_read_one_gender_success(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="read_one")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    gender_name = f"Spec-{uuid.uuid4().hex[:6]}"
    gender_data = {"name": gender_name, "long_name": "Gênero Específico Teste"}
    create_response = client.post("/genders/create", json=gender_data, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar gênero: {create_response.json()}"
    gender_id = create_response.json()["id"]
    
    response = client.get(f"/genders/read/{gender_id}", headers=headers)
    assert response.status_code == 200, f"Falha ao ler gênero: {response.json()}"
    data = response.json()
    assert data["id"] == gender_id
    assert data["name"] == gender_name

def test_read_one_gender_not_found(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="read_nf")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.get("/genders/read/99999999", headers=headers) 
    assert response.status_code == 404
    assert "Gênero não encontrado" in response.json()["detail"]

def test_update_gender_success(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="update_success")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    initial_name = f"OldGen-{uuid.uuid4().hex[:6]}"
    gender_data_initial = {"name": initial_name, "long_name": "Gênero Antigo"}
    create_response = client.post("/genders/create", json=gender_data_initial, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar gênero inicial: {create_response.json()}"
    gender_id = create_response.json()["id"]
    
    updated_name = f"NewGen-{uuid.uuid4().hex[:6]}"
    updated_long_name = "Gênero Novo Atualizado"
    update_data = {"name": updated_name, "long_name": updated_long_name}
    response = client.put(f"/genders/update/{gender_id}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Falha ao atualizar: {response.json()}"
    data = response.json()
    assert data["name"] == updated_name
    assert data["long_name"] == updated_long_name

def test_update_gender_not_found(client: TestClient, db_session: Session):
    user_token = get_gender_test_token(db_session, is_admin=False, unique_marker="update_nf")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    update_data = {"name": "NomeInexistente"}
    response = client.put("/genders/update/99999999", json=update_data, headers=headers)
    assert response.status_code == 404

def test_delete_gender_success_as_admin(client: TestClient, db_session: Session):
    admin_token = get_gender_test_token(db_session, is_admin=True, unique_marker="delete_admin") 
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    user_token_creator = get_gender_test_token(db_session, is_admin=False, unique_marker="delete_creator")
    headers_user_creator = {"Authorization": f"Bearer {user_token_creator}"}

    gender_name = f"ToDelete-{uuid.uuid4().hex[:6]}"
    gender_data = {"name": gender_name, "long_name": "Gênero Para Deletar"}
    create_response = client.post("/genders/create", json=gender_data, headers=headers_user_creator)
    assert create_response.status_code == 201, f"Erro ao criar gênero para deletar: {create_response.json()}"
    gender_id = create_response.json()["id"]
    
    response = client.delete(f"/genders/delete/{gender_id}", headers=headers_admin)
    assert response.status_code == 200, f"Falha ao deletar: {response.json()}"
    assert "deletado com sucesso" in response.json()["message"]

    db_gender = db_session.query(models.Gender).filter(models.Gender.id == gender_id).first()
    assert db_gender is None

def test_delete_gender_not_found_as_admin(client: TestClient, db_session: Session):
    admin_token = get_gender_test_token(db_session, is_admin=True, unique_marker="delete_nf_admin")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.delete("/genders/delete/99999999", headers=headers)
    assert response.status_code == 404

def test_delete_gender_forbidden_for_normal_user(client: TestClient, db_session: Session):
    user_token_creator_deleter = get_gender_test_token(db_session, is_admin=False, unique_marker="delete_forbidden_user")
    headers_user = {"Authorization": f"Bearer {user_token_creator_deleter}"}

    gender_name = f"Protected-{uuid.uuid4().hex[:6]}"
    gender_data = {"name": gender_name, "long_name": "Gênero Protegido"}
    create_response = client.post("/genders/create", json=gender_data, headers=headers_user)
    assert create_response.status_code == 201, f"Erro ao criar gênero protegido: {create_response.json()}"
    gender_id = create_response.json()["id"]

    response = client.delete(f"/genders/delete/{gender_id}", headers=headers_user)
    assert response.status_code == 403, f"Status inesperado: {response.json()}"
    assert "Acesso negado" in response.json()["detail"]