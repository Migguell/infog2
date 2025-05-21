# Conteúdo do arquivo: app/database/connection.py
# Este arquivo configura a conexão com o banco de dados PostgreSQL usando SQLAlchemy.

import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
from app.core.config import get_settings 

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def connect_to_db(max_retries: int = 10, delay: int = 5):
    print("Tentando conectar ao banco de dados...")
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Conexão com o banco de dados estabelecida com sucesso!")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Tentativa {attempt + 1}/{max_retries} falhou. Erro: {e}. Tentando novamente em {delay} segundos...")
                time.sleep(delay)
            else:
                print(f"Falha ao conectar ao banco de dados após {max_retries} tentativas. Erro final: {e}")
                raise
    return False

