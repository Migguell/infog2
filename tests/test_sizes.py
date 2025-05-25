from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import uuid

from app.database import models
from app.auth.services import get_password_hash
from app.core.dependencies import create_token_response

VALID_TEST_PASSWORD = "testpassword123"

def get_size_ops_test_token(db_session: Session, is_admin: bool, unique_marker: str = "") -> str:
    email_base = f"size_ops_test_{'admin' if is_admin else 'user'}"
    email_suffix = uuid.uuid4().hex[:8]
    email = f"{email_base}_{unique_marker}_{email_suffix}@example.com"
    
    cpf_flag = 'S1' if is_admin else 'S2' 
    cpf_hash_part = abs(hash(email)) % 10000000 
    cpf = (cpf_flag + str(cpf_hash_part).zfill(9))[:11]

    test_user = db_session.query(models.User).filter(models.User.email == email).first()
    if not test_user:
        test_user = models.User(
            name=f"Size Ops Test {'Admin' if is_admin else 'User'} {unique_marker} {email_suffix}",
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
        except Exception:
            db_session.rollback()
            raise
            
    token_data = create_token_response(subject_id=test_user.id, is_admin=test_user.is_admin)
    return token_data.access_token

def test_create_size_success(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="create_size")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    size_name = f"Size-{uuid.uuid4().hex[:6]}"
    size_long_name = f"Tamanho Teste {uuid.uuid4().hex[:8]}"
    size_data = {"name": size_name, "long_name": size_long_name}
    
    response = client.post("/sizes/create", json=size_data, headers=headers)
    assert response.status_code == 201, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["name"] == size_name
    assert data["long_name"] == size_long_name
    assert "id" in data
    
    db_size = db_session.query(models.Size).filter(models.Size.id == data["id"]).first()
    assert db_size is not None
    assert db_size.name == size_name

def test_create_size_duplicate_name(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="create_dup_size")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    size_name = "GG-DupTest" 
    existing = db_session.query(models.Size).filter(models.Size.name == size_name).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    size_data = {"name": size_name, "long_name": "GG para Teste de Duplicidade"}
    resp1 = client.post("/sizes/create", json=size_data, headers=headers)
    assert resp1.status_code == 201, f"Primeira criação falhou: {resp1.json()}"
    
    size_data_dup = {"name": size_name, "long_name": "Outra Descrição GG"}
    response = client.post("/sizes/create", json=size_data_dup, headers=headers) 
    assert response.status_code == 400
    assert "Tamanho com este nome já existe" in response.json()["detail"]

def test_read_sizes_list(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="read_list_size")
    headers = {"Authorization": f"Bearer {user_token}"}

    name1 = f"M-{uuid.uuid4().hex[:6]}"
    name2 = f"P-{uuid.uuid4().hex[:6]}"
    
    resp1 = client.post("/sizes/create", json={"name": name1, "long_name": "Médio Lista"}, headers=headers)
    assert resp1.status_code == 201, f"Erro ao criar tamanho {name1}: {resp1.json()}"
    resp2 = client.post("/sizes/create", json={"name": name2, "long_name": "Pequeno Lista"}, headers=headers)
    assert resp2.status_code == 201, f"Erro ao criar tamanho {name2}: {resp2.json()}"
    
    response = client.get("/sizes/read", headers=headers)
    assert response.status_code == 200, f"Erro ao ler tamanhos: {response.json()}"
    data = response.json()
    assert isinstance(data, list)
    
    names_in_response = [item["name"] for item in data]
    assert name1 in names_in_response
    assert name2 in names_in_response

def test_read_one_size_success(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="read_one_size")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    size_name = f"XG-{uuid.uuid4().hex[:6]}"
    size_data = {"name": size_name, "long_name": "Extra Grande Específico Teste"}
    create_response = client.post("/sizes/create", json=size_data, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar tamanho: {create_response.json()}"
    size_id = create_response.json()["id"]
    
    response = client.get(f"/sizes/read/{size_id}", headers=headers)
    assert response.status_code == 200, f"Falha ao ler tamanho: {response.json()}"
    data = response.json()
    assert data["id"] == size_id
    assert data["name"] == size_name

def test_read_one_size_not_found(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="read_nf_size")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.get("/sizes/read/999999999", headers=headers) 
    assert response.status_code == 404
    assert "Tamanho não encontrado" in response.json()["detail"]

def test_update_size_success(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="update_size")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    initial_name = f"OldS-{uuid.uuid4().hex[:6]}"
    size_data_initial = {"name": initial_name, "long_name": "Tamanho Antigo Para Update"}
    create_response = client.post("/sizes/create", json=size_data_initial, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar tamanho inicial: {create_response.json()}"
    size_id = create_response.json()["id"]
    
    updated_name = f"NewS-{uuid.uuid4().hex[:6]}"
    updated_long_name = f"Tamanho Novo Atualizado {uuid.uuid4().hex[:4]}"
    update_data = {"name": updated_name, "long_name": updated_long_name}
    response = client.put(f"/sizes/update/{size_id}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Falha ao atualizar: {response.json()}"
    data = response.json()
    assert data["name"] == updated_name
    assert data["long_name"] == updated_long_name

def test_update_size_not_found(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="update_nf_size")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    update_data = {"name": "NomeInexistenteSize"}
    response = client.put("/sizes/update/999999999", json=update_data, headers=headers)
    assert response.status_code == 404

def test_delete_size_success_as_admin(client: TestClient, db_session: Session):
    admin_token = get_size_ops_test_token(db_session, is_admin=True, unique_marker="delete_admin_size") 
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    user_token_creator = get_size_ops_test_token(db_session, is_admin=False, unique_marker="delete_creator_size")
    headers_user_creator = {"Authorization": f"Bearer {user_token_creator}"}

    size_name = f"ToDel-{uuid.uuid4().hex[:6]}"
    size_data = {"name": size_name, "long_name": "Tamanho Para Deletar"}
    create_response = client.post("/sizes/create", json=size_data, headers=headers_user_creator)
    assert create_response.status_code == 201, f"Erro ao criar tamanho para deletar: {create_response.json()}"
    size_id = create_response.json()["id"]
    
    response = client.delete(f"/sizes/delete/{size_id}", headers=headers_admin)
    assert response.status_code == 200, f"Falha ao deletar: {response.json()}"
    assert "deletado com sucesso" in response.json()["message"]

    db_size = db_session.query(models.Size).filter(models.Size.id == size_id).first()
    assert db_size is None

def test_delete_size_not_found_as_admin(client: TestClient, db_session: Session):
    admin_token = get_size_ops_test_token(db_session, is_admin=True, unique_marker="delete_nf_admin_size")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.delete("/sizes/delete/999999999", headers=headers)
    assert response.status_code == 404

def test_delete_size_forbidden_for_normal_user(client: TestClient, db_session: Session):
    user_token = get_size_ops_test_token(db_session, is_admin=False, unique_marker="delete_forbidden_size")
    headers = {"Authorization": f"Bearer {user_token}"}

    size_name = f"ProtectedS-{uuid.uuid4().hex[:6]}"
    size_data = {"name": size_name, "long_name": "Tamanho Protegido"}
    create_response = client.post("/sizes/create", json=size_data, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar tamanho protegido: {create_response.json()}"
    size_id = create_response.json()["id"]

    response = client.delete(f"/sizes/delete/{size_id}", headers=headers)
    assert response.status_code == 403, f"Status inesperado: {response.json()}"
    assert "Acesso negado" in response.json()["detail"]