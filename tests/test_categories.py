from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import uuid 

from app.database import models
from app.auth.services import get_password_hash
from app.core.dependencies import create_token_response

def get_test_token(db_session: Session, is_admin: bool, unique_marker: str = "") -> str:
    email_base = f"category_test_{'admin' if is_admin else 'user'}"
    email_suffix_num = abs(hash(f"{email_base}_{str(is_admin)}_{unique_marker}_{uuid.uuid4().hex}")) % 100000
    email = f"{email_base}_{email_suffix_num}@example.com"
    
    cpf_flag = '1' if is_admin else '2' 
    cpf_hash_part = abs(hash(email)) % 1000
    cpf = f"0000000{cpf_flag}{cpf_hash_part:03d}"
    
    test_user = db_session.query(models.User).filter(models.User.email == email).first()
    if not test_user:
        test_user = models.User(
            name=f"Category Test {'Admin' if is_admin else 'User'} {unique_marker}",
            email=email,
            cpf=cpf, 
            hashed_password=get_password_hash("testpassword"),
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


def test_create_category(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="create_cat")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    category_name = f"Eletrônicos Teste {uuid.uuid4().hex[:8]}"
    category_data = {"name": category_name}
    response = client.post("/categories/create", json=category_data, headers=headers)
    
    assert response.status_code == 201, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["name"] == category_data["name"]
    assert "id" in data
    
    db_category = db_session.query(models.Category).filter(models.Category.id == data["id"]).first()
    assert db_category is not None
    assert db_category.name == category_data["name"]

def test_create_category_duplicate_name(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="create_dup_cat")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    category_name = "Moda Teste Duplicado Categoria" 
    existing_category = db_session.query(models.Category).filter(models.Category.name == category_name).first()
    if existing_category:
        db_session.delete(existing_category)
        db_session.commit()

    category_data = {"name": category_name}
    resp1 = client.post("/categories/create", json=category_data, headers=headers)
    assert resp1.status_code == 201, f"Primeira criação falhou: {resp1.json()}"
    
    response = client.post("/categories/create", json=category_data, headers=headers) 
    assert response.status_code == 400
    assert "Categoria com este nome já existe" in response.json()["detail"]

def test_read_categories(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="read_list_cat")
    headers = {"Authorization": f"Bearer {user_token}"}

    name1 = f"Livros Cat {uuid.uuid4().hex[:8]}"
    name2 = f"Música Cat {uuid.uuid4().hex[:8]}"
    
    resp1 = client.post("/categories/create", json={"name": name1}, headers=headers)
    assert resp1.status_code == 201, f"Erro ao criar categoria {name1}: {resp1.json()}"
    resp2 = client.post("/categories/create", json={"name": name2}, headers=headers)
    assert resp2.status_code == 201, f"Erro ao criar categoria {name2}: {resp2.json()}"
    
    response = client.get("/categories/read", headers=headers)
    assert response.status_code == 200, f"Erro ao ler categorias: {response.json()}"
    data = response.json()
    assert isinstance(data, list)
    
    names_in_response = [item["name"] for item in data]
    assert name1 in names_in_response, f"{name1} não encontrado em {names_in_response}"
    assert name2 in names_in_response, f"{name2} não encontrado em {names_in_response}"

def test_read_one_category(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="read_one_cat")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    category_name = f"Jogos Cat {uuid.uuid4().hex[:8]}"
    category_data = {"name": category_name}
    create_response = client.post("/categories/create", json=category_data, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar categoria: {create_response.json()}"
    category_id = create_response.json()["id"]
    
    response = client.get(f"/categories/read/{category_id}", headers=headers)
    assert response.status_code == 200, f"Falha ao ler categoria: {response.json()}"
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == category_data["name"]

def test_read_one_category_not_found(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="read_nf_cat")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.get("/categories/read/99999999", headers=headers) 
    assert response.status_code == 404

def test_update_category(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="update_cat")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    initial_name = f"Software Antigo Cat {uuid.uuid4().hex[:8]}"
    category_data_initial = {"name": initial_name}
    create_response = client.post("/categories/create", json=category_data_initial, headers=headers)
    assert create_response.status_code == 201, f"Erro ao criar categoria inicial: {create_response.json()}"
    category_id = create_response.json()["id"]
    
    updated_name = f"Software Novo Cat {uuid.uuid4().hex[:8]}"
    update_data = {"name": updated_name}
    response = client.put(f"/categories/update/{category_id}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Falha ao atualizar: {response.json()}"
    data = response.json()
    assert data["name"] == update_data["name"]

def test_update_category_not_found(client: TestClient, db_session: Session):
    user_token = get_test_token(db_session, is_admin=False, unique_marker="update_nf_cat")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    update_data = {"name": "Nome Inexistente"}
    response = client.put("/categories/update/99999999", json=update_data, headers=headers)
    assert response.status_code == 404
    
def test_delete_category(client: TestClient, db_session: Session):
    admin_token = get_test_token(db_session, is_admin=True, unique_marker="delete_admin_cat") 
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    user_token_creator = get_test_token(db_session, is_admin=False, unique_marker="delete_creator_cat")
    headers_user_creator = {"Authorization": f"Bearer {user_token_creator}"}

    category_name = f"Categoria Para Deletar Cat {uuid.uuid4().hex[:8]}"
    category_data = {"name": category_name}
    create_response = client.post("/categories/create", json=category_data, headers=headers_user_creator)
    assert create_response.status_code == 201, f"Erro ao criar categoria para deletar: {create_response.json()}"
    category_id = create_response.json()["id"]
    
    response = client.delete(f"/categories/delete/{category_id}", headers=headers_admin)
    assert response.status_code == 200, f"Falha ao deletar: {response.json()}"

def test_delete_category_not_found(client: TestClient, db_session: Session):
    admin_token = get_test_token(db_session, is_admin=True, unique_marker="delete_nf_admin_cat")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.delete("/categories/delete/99999999", headers=headers)
    assert response.status_code == 404

def test_delete_category_forbidden_for_normal_user(client: TestClient, db_session: Session):
    user_token_creator = get_test_token(db_session, is_admin=False, unique_marker="delete_forbidden_creator_cat")
    headers_user_creator = {"Authorization": f"Bearer {user_token_creator}"}

    category_name = f"Categoria Protegida Cat {uuid.uuid4().hex[:8]}"
    category_data = {"name": category_name}
    create_response = client.post("/categories/create", json=category_data, headers=headers_user_creator)
    assert create_response.status_code == 201, f"Erro ao criar categoria protegida: {create_response.json()}"
    category_id = create_response.json()["id"]

    response = client.delete(f"/categories/delete/{category_id}", headers=headers_user_creator)
    assert response.status_code == 403, f"Status inesperado: {response.json()}"
    assert "Acesso negado" in response.json()["detail"]