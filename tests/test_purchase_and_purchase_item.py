from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import uuid
from decimal import Decimal

from app.database import models
from app.auth.services import get_password_hash
from app.core.dependencies import create_token_response

VALID_TEST_PASSWORD = "testpassword123"

def get_purchase_ops_test_token(db_session: Session, is_admin: bool, unique_marker: str = "") -> str:
    email_base = f"purchase_ops_test_{'admin' if is_admin else 'user'}"
    email_suffix = uuid.uuid4().hex[:8]
    email = f"{email_base}_{unique_marker}_{email_suffix}@example.com"
    
    cpf_flag = 'PU1' if is_admin else 'PU2' 
    cpf_hash_part = abs(hash(email)) % 10000000 
    cpf = (cpf_flag + str(cpf_hash_part).zfill(9))[:11]

    test_user = db_session.query(models.User).filter(models.User.email == email).first()
    if not test_user:
        test_user = models.User(
            name=f"Purchase Ops {'Admin' if is_admin else 'User'} {unique_marker} {email_suffix}",
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

@pytest.fixture(scope="function")
def created_purchase_prerequisites(db_session: Session, client: TestClient):
    user_token = get_purchase_ops_test_token(db_session, is_admin=False, unique_marker="prereq_user_pur")
    headers = {"Authorization": f"Bearer {user_token}"}

    size_name = f"SizePur-{uuid.uuid4().hex[:4]}"
    size_resp = client.post("/sizes/create", json={"name": size_name, "long_name": "Tamanho para Pedido"}, headers=headers)
    assert size_resp.status_code == 201, f"Falha ao criar size: {size_resp.json()}"
    size_id = size_resp.json()["id"]

    category_name = f"CatPur-{uuid.uuid4().hex[:4]}"
    cat_resp = client.post("/categories/create", json={"name": category_name}, headers=headers)
    assert cat_resp.status_code == 201, f"Falha ao criar category: {cat_resp.json()}"
    category_id = cat_resp.json()["id"]

    gender_name = f"GenPur-{uuid.uuid4().hex[:4]}"
    gender_resp = client.post("/genders/create", json={"name": gender_name, "long_name": "Gênero para Pedido"}, headers=headers)
    assert gender_resp.status_code == 201, f"Falha ao criar gender: {gender_resp.json()}"
    gender_id = gender_resp.json()["id"]

    product1_name = f"ProdPur1-{uuid.uuid4().hex[:8]}"
    product1_price_str = "25.50"
    product1_inventory = 20
    prod1_data = {
        "name": product1_name, "description": "Produto 1 para Pedido", "price": product1_price_str, 
        "inventory": product1_inventory, "size_id": size_id, "category_id": category_id, "gender_id": gender_id
    }
    prod1_resp = client.post("/products/create", json=prod1_data, headers=headers)
    assert prod1_resp.status_code == 201, f"Falha ao criar produto 1: {prod1_resp.json()}"
    product1_id = prod1_resp.json()["id"]

    product2_name = f"ProdPur2-{uuid.uuid4().hex[:8]}"
    product2_price_str = "10.75"
    product2_inventory = 15
    prod2_data = {
        "name": product2_name, "description": "Produto 2 para Pedido", "price": product2_price_str, 
        "inventory": product2_inventory, "size_id": size_id, "category_id": category_id, "gender_id": gender_id
    }
    prod2_resp = client.post("/products/create", json=prod2_data, headers=headers)
    assert prod2_resp.status_code == 201, f"Falha ao criar produto 2: {prod2_resp.json()}"
    product2_id = prod2_resp.json()["id"]

    client_email = f"client.pur.{uuid.uuid4().hex[:6]}@example.com"
    client_cpf = f"77788890{abs(hash(client_email))%1000:03d}"
    client_payload = {"name": "Cliente De Pedido", "email": client_email, "cpf": client_cpf, "password": VALID_TEST_PASSWORD}
    client_resp = client.post("/clients/create", json=client_payload)
    assert client_resp.status_code == 201, f"Falha ao criar cliente: {client_resp.json()}"
    client_id = client_resp.json()["client"]["id"]

    return {
        "user_token": user_token,
        "admin_token": get_purchase_ops_test_token(db_session, is_admin=True, unique_marker="prereq_admin_pur"),
        "client_id": client_id,
        "product1_id": product1_id, "product1_price": Decimal(product1_price_str), "product1_inventory": product1_inventory,
        "product2_id": product2_id, "product2_price": Decimal(product2_price_str), "product2_inventory": product2_inventory,
        "size_id": size_id
    }

def test_create_purchase_success(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    headers = {"Authorization": f"Bearer {deps['user_token']}"}

    purchase_items_data = [
        {"product_id": deps["product1_id"], "size_id": deps["size_id"], "quantity": 2, "unit_price_at_purchase": str(deps["product1_price"])},
        {"product_id": deps["product2_id"], "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": str(deps["product2_price"])}
    ]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}

    response = client.post("/purchases/create", json=purchase_data, headers=headers)
    assert response.status_code == 201, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["client_id"] == deps["client_id"]
    assert data["status"] == "pending"
    assert len(data["items"]) == 2
    
    expected_subtotal = (Decimal("2") * deps["product1_price"]) + (Decimal("1") * deps["product2_price"])
    assert Decimal(data["subtotal"]) == expected_subtotal

    prod1_after = db_session.query(models.Product).filter(models.Product.id == uuid.UUID(deps["product1_id"])).first()
    assert prod1_after.inventory == deps["product1_inventory"] - 2
    prod2_after = db_session.query(models.Product).filter(models.Product.id == uuid.UUID(deps["product2_id"])).first()
    assert prod2_after.inventory == deps["product2_inventory"] - 1

def test_create_purchase_insufficient_inventory(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    headers = {"Authorization": f"Bearer {deps['user_token']}"}

    purchase_items_data = [
        {"product_id": deps["product1_id"], "size_id": deps["size_id"], 
         "quantity": deps["product1_inventory"] + 1, 
         "unit_price_at_purchase": str(deps["product1_price"])}
    ]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}

    response = client.post("/purchases/create", json=purchase_data, headers=headers)
    assert response.status_code == 400
    assert "Estoque insuficiente" in response.json()["detail"]

def test_create_purchase_client_not_found(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    headers = {"Authorization": f"Bearer {deps['user_token']}"}
    
    non_existent_client_id = str(uuid.uuid4())
    purchase_items_data = [
        {"product_id": deps["product1_id"], "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": str(deps["product1_price"])}
    ]
    purchase_data = {"client_id": non_existent_client_id, "items": purchase_items_data}

    response = client.post("/purchases/create", json=purchase_data, headers=headers)
    assert response.status_code == 404
    assert "Cliente não encontrado" in response.json()["detail"]

def test_create_purchase_product_not_found(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    headers = {"Authorization": f"Bearer {deps['user_token']}"}
    
    non_existent_product_id = str(uuid.uuid4())
    purchase_items_data = [
        {"product_id": non_existent_product_id, "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": "10.00"}
    ]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}

    response = client.post("/purchases/create", json=purchase_data, headers=headers)
    assert response.status_code == 404
    assert f"Produto com ID {non_existent_product_id} não encontrado" in response.json()["detail"]


def test_read_purchases_list(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    headers = {"Authorization": f"Bearer {deps['user_token']}"}

    create_resp = client.post("/purchases/create", 
                json={
                    "client_id": deps["client_id"], 
                    "items": [{"product_id": deps["product2_id"], "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": str(deps["product2_price"])}]
                }, 
                headers=headers)
    assert create_resp.status_code == 201, f"Falha ao criar pedido para teste de lista: {create_resp.json()}"

    response = client.get("/purchases/read", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["client_id"] == deps["client_id"] for item in data)

def test_read_one_purchase_success(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    headers = {"Authorization": f"Bearer {deps['user_token']}"}

    purchase_items_data = [{"product_id": deps["product1_id"], "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": str(deps["product1_price"])}]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}
    create_resp = client.post("/purchases/create", json=purchase_data, headers=headers)
    assert create_resp.status_code == 201
    purchase_id = create_resp.json()["id"]

    response = client.get(f"/purchases/read/{purchase_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == purchase_id

def test_update_purchase_status_success(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    user_token = deps["user_token"] 
    headers = {"Authorization": f"Bearer {user_token}"}

    purchase_items_data = [{"product_id": deps["product1_id"], "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": str(deps["product1_price"])}]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}
    create_resp = client.post("/purchases/create", json=purchase_data, headers=headers)
    assert create_resp.status_code == 201
    purchase_id = create_resp.json()["id"]

    update_payload = {"status": "shipped"}
    response = client.put(f"/purchases/update/{purchase_id}", json=update_payload, headers=headers)
    assert response.status_code == 200, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["status"] == "shipped"

def test_delete_purchase_success_as_admin(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    user_headers = {"Authorization": f"Bearer {deps['user_token']}"}
    admin_headers = {"Authorization": f"Bearer {deps['admin_token']}"}

    quantity_ordered = 2
    purchase_items_data = [{"product_id": deps["product1_id"], "size_id": deps["size_id"], "quantity": quantity_ordered, "unit_price_at_purchase": str(deps["product1_price"])}]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}
    create_resp = client.post("/purchases/create", json=purchase_data, headers=user_headers)
    assert create_resp.status_code == 201
    purchase_id = create_resp.json()["id"]
    
    prod1 = db_session.query(models.Product).filter(models.Product.id == uuid.UUID(deps["product1_id"])).first()
    assert prod1 is not None
    inventory_before_purchase_deletion = prod1.inventory 
    
    delete_resp = client.delete(f"/purchases/delete/{purchase_id}", headers=admin_headers)
    assert delete_resp.status_code == 200, f"Detalhe: {delete_resp.json()}"
    assert "deletado com sucesso" in delete_resp.json()["message"]

    assert db_session.query(models.Purchase).filter(models.Purchase.id == uuid.UUID(purchase_id)).first() is None
    
    db_session.refresh(prod1) 
    assert prod1.inventory == inventory_before_purchase_deletion + quantity_ordered

def test_delete_purchase_forbidden_for_normal_user(client: TestClient, db_session: Session, created_purchase_prerequisites):
    deps = created_purchase_prerequisites
    user_headers = {"Authorization": f"Bearer {deps['user_token']}"}

    purchase_items_data = [{"product_id": deps["product1_id"], "size_id": deps["size_id"], "quantity": 1, "unit_price_at_purchase": str(deps["product1_price"])}]
    purchase_data = {"client_id": deps["client_id"], "items": purchase_items_data}
    create_resp = client.post("/purchases/create", json=purchase_data, headers=user_headers)
    assert create_resp.status_code == 201
    purchase_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/purchases/delete/{purchase_id}", headers=user_headers)
    assert delete_resp.status_code == 403
    assert "Acesso negado" in delete_resp.json()["detail"]