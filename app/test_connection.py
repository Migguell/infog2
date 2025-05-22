import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a URL de conexão do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    connection = None  # Inicializar a variável connection
    try:
        # Tentar se conectar ao banco de dados
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()
        
        # Executar uma consulta simples
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        print("Conexão bem-sucedida! Resultado da consulta:", result)
        
    except Exception as e:
        print("Erro ao conectar ao banco de dados:", e)
    finally:
        # Fechar a conexão
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    test_connection()
