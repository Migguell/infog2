import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app.main import app
from app.database.connection import Base, get_db
from app.core.config import get_settings

if os.path.exists(os.path.join(PROJECT_ROOT, ".env.test")):
    load_dotenv(os.path.join(PROJECT_ROOT, ".env.test"))
else:
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

settings = get_settings()

DEFAULT_TEST_DB_NAME_SUFFIX = "_test"
if "DATABASE_URL" in os.environ:
    DATABASE_URL = os.environ["DATABASE_URL"]
else:
    if settings.DATABASE_URL:
        parts = settings.DATABASE_URL.split('/')
        db_name_with_suffix = parts[-1] + DEFAULT_TEST_DB_NAME_SUFFIX
        parts[-1] = db_name_with_suffix
        DATABASE_URL = '/'.join(parts)
    else:
        DATABASE_URL = "postgresql://user:password@localhost:5432/infog2_test_db"
        print(f"AVISO: DATABASE_URL não definida e DATABASE_URL principal também não. Usando fallback: {DATABASE_URL}")

print(f"Usando banco de dados de teste: {DATABASE_URL}")

engine = create_engine(
    DATABASE_URL,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_database_tables():
    """
    Fixture com escopo de sessão para criar todas as tabelas no banco de dados
    de teste antes de qualquer teste rodar, e removê-las depois que todos os testes
    da sessão forem concluídos. 'autouse=True' faz com que seja executada automaticamente.
    """
    print(f"Criando tabelas no banco de dados de teste: {DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso.")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        raise
    yield
    print(f"Removendo tabelas do banco de dados de teste: {DATABASE_URL}")
    try:
        Base.metadata.drop_all(bind=engine)
        print("Tabelas removidas com sucesso.")
    except Exception as e:
        print(f"Erro ao remover tabelas: {e}")
        raise


@pytest.fixture(scope="function")
def db_session(create_test_database_tables) -> SQLAlchemySession:
    """
    Fixture com escopo de função para fornecer uma sessão de banco de dados
    transacional para cada teste.
    A transação é revertida após cada teste para garantir isolamento.
    """
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)

    original_get_db = app.dependency_overrides.get(get_db)
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()
        if original_get_db:
            app.dependency_overrides[get_db] = original_get_db
        else:
            del app.dependency_overrides[get_db]


@pytest.fixture(scope="session")
def client(create_test_database_tables) -> TestClient:
    """
    Fixture para fornecer um TestClient da API FastAPI.
    """
    api_client = TestClient(app)
    return api_client