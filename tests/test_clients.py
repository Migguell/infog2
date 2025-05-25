from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import uuid

from app.database import models
from app.auth.services import get_password_hash
from app.core.dependencies import create_token_response

VALID_PASSWORD = "password123"

def get_client_ops_test_token(db_session: Session, client: TestClient, is_admin: bool, unique_marker: str = "") -> str:
    """
    Cria um usuário de teste (models.User) se não existir PARA ESTA SESSÃO/CHAMADA 
    e retorna um token para ele. Não usa cache global de token.
    """
    email_base = f"client_ops_test_{'admin' if is_admin else 'user'}"
    email_suffix_num = abs(hash(f"{email_base}_{str(is_admin)}_{unique_marker}_{uuid.uuid4().hex}")) % 100000 
    email = f"{email_base}_{email_suffix_num}@example.com"
    
    cpf_flag = '3' if is_admin else '4' 
    cpf_hash_part = abs(hash(email)) % 1000 
    cpf = f"0000000{cpf_flag}{cpf_hash_part:03d}"

    test_user = models.User(
        name=f"Client Ops Test {'Admin' if is_admin else 'User'} {unique_marker}",
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

def test_create_client_success(client: TestClient, db_session: Session):
    client_email = f"novocliente.valido.{uuid.uuid4().hex[:8]}@example.com"
    client_cpf = f"1231231{abs(hash(client_email))%10000:04d}"
    client_data = {
        "name": "Novo Cliente Teste Válido",
        "email": client_email,
        "cpf": client_cpf,
        "password": VALID_PASSWORD
    }
    response = client.post("/clients/create", json=client_data)
    assert response.status_code == 201, f"Detalhe do erro: {response.json()}"
    data = response.json()
    assert "client" in data
    assert data["client"]["name"] == client_data["name"]
    
    db_client_check = db_session.query(models.Client).filter(models.Client.email == client_data["email"]).first()
    assert db_client_check is not None

def test_create_client_duplicate_email(client: TestClient, db_session: Session):
    fixed_email = "client.dup.email.check@example.com"
    cpf1 = f"2342342{abs(hash(f'{fixed_email}1'))%10000:04d}"
    cpf2 = f"2342342{(abs(hash(f'{fixed_email}2'))+1)%10000:04d}"

    client_data1 = {"name": "Cliente Email Unico DupCheck", "email": fixed_email, "cpf": cpf1, "password": VALID_PASSWORD}
    resp1 = client.post("/clients/create", json=client_data1)
    assert resp1.status_code == 201, f"Falha ao criar cliente base (cpf1: {cpf1}): {resp1.json()}"

    client_data2 = {"name": "Cliente Email Duplicado Tentativa", "email": fixed_email, "cpf": cpf2, "password": "passwordcliente2"}
    response = client.post("/clients/create", json=client_data2)
    assert response.status_code == 400
    assert "Email já registrado" in response.json()["detail"]

def test_create_client_duplicate_cpf(client: TestClient, db_session: Session):
    fixed_cpf = "34534534500"
    email1 = f"client.cpf.unico.check.{uuid.uuid4().hex[:6]}@example.com"
    email2 = f"client.cpf.dup.email.check.{uuid.uuid4().hex[:6]}@example.com"
    
    client_data1 = {"name": "Cliente CPF Unico DupCheck", "email": email1, "cpf": fixed_cpf, "password": VALID_PASSWORD}
    resp1 = client.post("/clients/create", json=client_data1)
    assert resp1.status_code == 201, f"Falha ao criar cliente base: {resp1.json()}"
    
    client_data2 = {"name": "Cliente CPF Duplicado Tentativa", "email": email2, "cpf": fixed_cpf, "password": "passwordcliente2"}
    response = client.post("/clients/create", json=client_data2)
    assert response.status_code == 400
    assert "CPF já registrado" in response.json()["detail"]

def test_read_clients_as_user(client: TestClient, db_session: Session):
    user_token = get_client_ops_test_token(db_session, client, is_admin=False, unique_marker="read_list")
    headers = {"Authorization": f"Bearer {user_token}"}

    email_a = f"cl.read.a.{uuid.uuid4().hex[:6]}@example.com"
    cpf_a = f"4564564{abs(hash(email_a))%10000:04d}"
    resp_a = client.post("/clients/create", json={"name": "Cliente Leitura A", "email": email_a, "cpf": cpf_a, "password": VALID_PASSWORD})
    assert resp_a.status_code == 201, f"Falha ao criar Cliente A: {resp_a.json()}"
    
    email_b = f"cl.read.b.{uuid.uuid4().hex[:6]}@example.com"
    cpf_b = f"4564564{(abs(hash(email_b))+1)%10000:04d}" 
    resp_b = client.post("/clients/create", json={"name": "Cliente Leitura B", "email": email_b, "cpf": cpf_b, "password": VALID_PASSWORD})
    assert resp_b.status_code == 201, f"Falha ao criar Cliente B: {resp_b.json()}"

    response = client.get("/clients/read", headers=headers)
    assert response.status_code == 200, f"Falha ao ler clientes: {response.json()}"
    data = response.json()
    assert isinstance(data, list)
    
    names_in_response = [c["name"] for c in data]
    assert "Cliente Leitura A" in names_in_response
    assert "Cliente Leitura B" in names_in_response

def test_read_one_client_as_user(client: TestClient, db_session: Session):
    user_token = get_client_ops_test_token(db_session, client, is_admin=False, unique_marker="read_one")
    headers = {"Authorization": f"Bearer {user_token}"}

    unique_email = f"cl.readone.{uuid.uuid4().hex[:8]}@example.com"
    unique_cpf = f"5675675{abs(hash(unique_email))%10000:04d}"
    client_data = {"name": "Cliente Para Leitura Unica", "email": unique_email, "cpf": unique_cpf, "password": VALID_PASSWORD}
    
    create_resp = client.post("/clients/create", json=client_data)
    assert create_resp.status_code == 201, f"Falha ao criar cliente para leitura: {create_resp.json()}"
    client_id = create_resp.json()["client"]["id"]

    response = client.get(f"/clients/read/{client_id}", headers=headers)
    assert response.status_code == 200, f"Falha ao ler cliente {client_id}: {response.json()}"
    data = response.json()
    assert data["id"] == client_id

def test_update_client_as_user(client: TestClient, db_session: Session):
    user_token = get_client_ops_test_token(db_session, client, is_admin=False, unique_marker="update")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    initial_email = f"cl.updateinit.{uuid.uuid4().hex[:8]}@example.com"
    initial_cpf = f"6786786{abs(hash(initial_email))%10000:04d}"
    client_data_initial = {"name": "Cliente Para Atualizar", "email": initial_email, "cpf": initial_cpf, "password": VALID_PASSWORD}
    
    create_resp = client.post("/clients/create", json=client_data_initial)
    assert create_resp.status_code == 201, f"Falha ao criar cliente para atualização: {create_resp.json()}"
    client_id = create_resp.json()["client"]["id"]

    updated_email = f"cl.updated.{uuid.uuid4().hex[:8]}@example.com"
    update_data = {"name": "Cliente Atualizado Nome Test", "email": updated_email}
    response = client.put(f"/clients/update/{client_id}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Falha ao atualizar cliente {client_id}: {response.json()}"
    data = response.json()
    assert data["name"] == update_data["name"]

def test_delete_client_as_admin(client: TestClient, db_session: Session):
    admin_token = get_client_ops_test_token(db_session, client, is_admin=True, unique_marker="delete_admin")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    delete_email = f"cl.delete.{uuid.uuid4().hex[:8]}@example.com"
    delete_cpf = f"7897897{abs(hash(delete_email))%10000:04d}"
    client_data = {"name": "Cliente Para Deletar Test", "email": delete_email, "cpf": delete_cpf, "password": VALID_PASSWORD}
    
    create_resp = client.post("/clients/create", json=client_data)
    assert create_resp.status_code == 201, f"Falha ao criar cliente para deleção: {create_resp.json()}"
    client_id_str = create_resp.json()["client"]["id"]
    
    response = client.delete(f"/clients/delete/{client_id_str}", headers=headers_admin)
    assert response.status_code == 200, f"Falha ao deletar cliente {client_id_str}: {response.json()}"
    assert "deletado com sucesso" in response.json()["message"]

def test_delete_client_forbidden_for_normal_user(client: TestClient, db_session: Session):
    untouchable_email = f"cl.untouchable.{uuid.uuid4().hex[:8]}@example.com"
    untouchable_cpf = f"8908908{abs(hash(untouchable_email))%10000:04d}"
    client_data = {"name": "Cliente Intocavel Test", "email": untouchable_email, "cpf": untouchable_cpf, "password": VALID_PASSWORD} 
    
    create_resp = client.post("/clients/create", json=client_data)
    assert create_resp.status_code == 201, f"Falha ao criar cliente para teste de deleção proibida: {create_resp.json()}"
    client_id = create_resp.json()["client"]["id"]

    user_token_deleter = get_client_ops_test_token(db_session, client, is_admin=False, unique_marker="delete_forbidden") 
    headers_user_deleter = {"Authorization": f"Bearer {user_token_deleter}"}

    response = client.delete(f"/clients/delete/{client_id}", headers=headers_user_deleter)
    assert response.status_code == 403, f"Status code inesperado: {response.json()}"
    assert "Acesso negado" in response.json()["detail"]