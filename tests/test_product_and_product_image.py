from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import uuid
from decimal import Decimal

from app.database import models
from app.auth.services import get_password_hash
from app.core.dependencies import create_token_response

VALID_TEST_PASSWORD = "testpassword123"

def get_prod_img_ops_test_token(db_session: Session, is_admin: bool, unique_marker: str = "") -> str:
    email_base = f"prodimg_ops_test_{'admin' if is_admin else 'user'}"
    email_suffix = uuid.uuid4().hex[:8]
    email = f"{email_base}_{unique_marker}_{email_suffix}@example.com"
    
    cpf_flag = 'PI1' if is_admin else 'PI2' 
    cpf_hash_part = abs(hash(email)) % 10000000 
    cpf = (cpf_flag + str(cpf_hash_part).zfill(8))[:11]

    test_user = db_session.query(models.User).filter(models.User.email == email).first()
    if not test_user:
        test_user = models.User(
            name=f"ProdImg Ops Test {'Admin' if is_admin else 'User'} {unique_marker} {email_suffix}",
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
def created_product_dependencies(db_session: Session, client: TestClient):
    user_token = get_prod_img_ops_test_token(db_session, is_admin=False, unique_marker="prod_deps")
    headers = {"Authorization": f"Bearer {user_token}"}

    size_name = f"SizeProd-{uuid.uuid4().hex[:4]}"
    size_resp = client.post("/sizes/create", json={"name": size_name}, headers=headers)
    assert size_resp.status_code == 201
    size_id = size_resp.json()["id"]

    category_name = f"CatProd-{uuid.uuid4().hex[:4]}"
    cat_resp = client.post("/categories/create", json={"name": category_name}, headers=headers)
    assert cat_resp.status_code == 201
    category_id = cat_resp.json()["id"]

    gender_name = f"GenProd-{uuid.uuid4().hex[:4]}"
    gender_resp = client.post("/genders/create", json={"name": gender_name}, headers=headers)
    assert gender_resp.status_code == 201
    gender_id = gender_resp.json()["id"]
    
    base_product_name = f"BaseProdForImg-{uuid.uuid4().hex[:8]}"
    base_product_data = {
        "name": base_product_name, "description": "Base product", "price": "1.00", "inventory": 1,
        "size_id": size_id, "category_id": category_id, "gender_id": gender_id
    }
    base_prod_resp = client.post("/products/create", json=base_product_data, headers=headers)
    assert base_prod_resp.status_code == 201
    base_product_id = base_prod_resp.json()["id"]

    img1_url = f"http://images.example.com/img1_{uuid.uuid4().hex[:4]}.png"
    img1_resp = client.post("/product-images/create", 
                            json={"product_id": base_product_id, "url": img1_url, "is_main": True}, 
                            headers=headers)
    assert img1_resp.status_code == 201
    image1_id = img1_resp.json()["id"]

    img2_url = f"http://images.example.com/img2_{uuid.uuid4().hex[:4]}.png"
    img2_resp = client.post("/product-images/create", 
                            json={"product_id": base_product_id, "url": img2_url, "is_main": False}, 
                            headers=headers)
    assert img2_resp.status_code == 201
    image2_id = img2_resp.json()["id"]

    return {
        "size_id": size_id, 
        "category_id": category_id, 
        "gender_id": gender_id,
        "image1_id": image1_id,
        "image2_id": image2_id,
        "base_product_id_for_images": base_product_id,
        "user_token": user_token,
        "admin_token": get_prod_img_ops_test_token(db_session, is_admin=True, unique_marker="prod_deps_admin")
    }

def test_create_product_success(client: TestClient, db_session: Session, created_product_dependencies):
    deps = created_product_dependencies
    headers = {"Authorization": f"Bearer {deps['user_token']}"}
    
    product_name = f"Camiseta Teste Prod {uuid.uuid4().hex[:8]}"
    product_data = {
        "name": product_name,
        "description": "Descrição da Camiseta Teste Prod.",
        "price": "149.99",
        "inventory": 50,
        "size_id": deps["size_id"],
        "category_id": deps["category_id"],
        "gender_id": deps["gender_id"],
        "product_image_ids": [deps["image1_id"], deps["image2_id"]]
    }
    response = client.post("/products/create", json=product_data, headers=headers)
    assert response.status_code == 201, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["name"] == product_name
    assert len(data["images"]) == 2
    assert {img["id"] for img in data["images"]} == {deps["image1_id"], deps["image2_id"]}

    img1_db = db_session.query(models.ProductImage).filter(models.ProductImage.id == deps["image1_id"]).first()
    assert img1_db is not None
    assert img1_db.product_id == uuid.UUID(data["id"])


def test_read_products_list(client: TestClient, db_session: Session, created_product_dependencies):
    headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    name1 = f"Produto Lista Prod1 {uuid.uuid4().hex[:8]}"
    client.post("/products/create", json={
        "name": name1, "description": "P Lista 1", "price": "20.00", "inventory": 5,
        "size_id": created_product_dependencies["size_id"], 
        "category_id": created_product_dependencies["category_id"], 
        "gender_id": created_product_dependencies["gender_id"]
    }, headers=headers)

    response = client.get("/products/read", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(p["name"] == name1 for p in data)

def test_read_one_product_success(client: TestClient, db_session: Session, created_product_dependencies):
    headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    product_name = f"Produto Leitura Unica Prod {uuid.uuid4().hex[:8]}"
    
    create_data = {
        "name": product_name, "description": "Desc Leitura Unica Prod", "price": "30.00", "inventory": 12,
        "size_id": created_product_dependencies["size_id"], 
        "category_id": created_product_dependencies["category_id"], 
        "gender_id": created_product_dependencies["gender_id"],
        "product_image_ids": [created_product_dependencies["image1_id"]]
    }
    create_resp = client.post("/products/create", json=create_data, headers=headers)
    assert create_resp.status_code == 201
    product_id = create_resp.json()["id"]

    response = client.get(f"/products/read/{product_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == product_name
    assert len(data["images"]) == 1
    assert data["images"][0]["id"] == created_product_dependencies["image1_id"]

def test_update_product_success(client: TestClient, db_session: Session, created_product_dependencies):
    headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    initial_name = f"Produto Update Init Prod {uuid.uuid4().hex[:8]}"
    create_data = {
        "name": initial_name, "description": "Desc Update Init Prod", "price": "40.00", "inventory": 15,
        "size_id": created_product_dependencies["size_id"], 
        "category_id": created_product_dependencies["category_id"], 
        "gender_id": created_product_dependencies["gender_id"]
    }
    create_resp = client.post("/products/create", json=create_data, headers=headers)
    assert create_resp.status_code == 201
    product_id = create_resp.json()["id"]

    updated_name = f"Produto Update Novo Nome Prod {uuid.uuid4().hex[:8]}"
    update_data = {"name": updated_name, "price": "45.50", "product_image_ids": [created_product_dependencies["image2_id"]]}
    
    response = client.put(f"/products/update/{product_id}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["name"] == updated_name
    assert Decimal(data["price"]) == Decimal("45.50")
    assert len(data["images"]) == 1
    assert data["images"][0]["id"] == created_product_dependencies["image2_id"]

def test_delete_product_success_as_admin(client: TestClient, db_session: Session, created_product_dependencies):
    user_headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    admin_headers = {"Authorization": f"Bearer {created_product_dependencies['admin_token']}"}
    
    product_name = f"Produto Deletar Admin Prod {uuid.uuid4().hex[:8]}"
    create_data = {
        "name": product_name, "description": "Desc Deletar Admin Prod", "price": "50.00", "inventory": 5,
        "size_id": created_product_dependencies["size_id"], 
        "category_id": created_product_dependencies["category_id"], 
        "gender_id": created_product_dependencies["gender_id"],
        "product_image_ids": [created_product_dependencies["image1_id"]]
    }
    create_resp = client.post("/products/create", json=create_data, headers=user_headers)
    assert create_resp.status_code == 201
    product_id = create_resp.json()["id"]
    
    img1_before_delete = db_session.query(models.ProductImage).get(created_product_dependencies["image1_id"])
    assert img1_before_delete is not None
    assert img1_before_delete.product_id == uuid.UUID(product_id)

    delete_resp = client.delete(f"/products/delete/{product_id}", headers=admin_headers)
    assert delete_resp.status_code == 200
    
    assert db_session.query(models.Product).filter(models.Product.id == uuid.UUID(product_id)).first() is None
    assert db_session.query(models.ProductImage).filter(models.ProductImage.id == created_product_dependencies["image1_id"]).first() is None


def test_create_product_image_success(client: TestClient, db_session: Session, created_product_dependencies):
    user_token = created_product_dependencies["user_token"]
    headers = {"Authorization": f"Bearer {user_token}"}
    product_id_for_new_image = created_product_dependencies["base_product_id_for_images"]

    image_url = f"http://example.com/another_image_{uuid.uuid4().hex[:6]}.jpg"
    image_data = {
        "product_id": product_id_for_new_image,
        "url": image_url,
        "description": "Outra Imagem de Produto Teste",
        "is_main": False
    }
    response = client.post("/product-images/create", json=image_data, headers=headers)
    assert response.status_code == 201, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["url"] == image_url
    assert data["product_id"] == product_id_for_new_image

def test_read_product_images_for_a_product(client: TestClient, db_session: Session, created_product_dependencies):
    headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    product_id_to_query = created_product_dependencies["base_product_id_for_images"]

    response = client.get(f"/product-images/read?product_id={product_id_to_query}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    found_ids = {img["id"] for img in data}
    assert created_product_dependencies["image1_id"] in found_ids
    assert created_product_dependencies["image2_id"] in found_ids

def test_read_one_product_image_success(client: TestClient, db_session: Session, created_product_dependencies):
    headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    image_id_to_read = created_product_dependencies["image1_id"]

    response = client.get(f"/product-images/read/{image_id_to_read}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == image_id_to_read

def test_update_product_image_success(client: TestClient, db_session: Session, created_product_dependencies):
    headers = {"Authorization": f"Bearer {created_product_dependencies['user_token']}"}
    image_id_to_update = created_product_dependencies["image2_id"]

    updated_description = f"Descrição Atualizada Imagem {uuid.uuid4().hex[:4]}"
    update_data = {"description": updated_description, "is_main": True}
    
    response = client.put(f"/product-images/update/{image_id_to_update}", json=update_data, headers=headers)
    assert response.status_code == 200, f"Detalhe: {response.json()}"
    data = response.json()
    assert data["description"] == updated_description
    assert data["is_main"] is True

def test_delete_product_image_success_as_admin(client: TestClient, db_session: Session, created_product_dependencies):
    admin_headers = {"Authorization": f"Bearer {created_product_dependencies['admin_token']}"}
    image_id_to_delete = created_product_dependencies["image1_id"]

    delete_resp = client.delete(f"/product-images/delete/{image_id_to_delete}", headers=admin_headers)
    assert delete_resp.status_code == 200, f"Detalhe: {delete_resp.json()}"
    
    check_resp = client.get(f"/product-images/read/{image_id_to_delete}", headers=admin_headers)
    assert check_resp.status_code == 404