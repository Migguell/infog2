# Infog2 API - Lu Estilo

API RESTful desenvolvida para gerenciar clientes, produtos, pedidos e outras entidades para o sistema Lu Estilo.

## Funcionalidades

A API oferece funcionalidades CRUD (Criar, Ler, Atualizar, Deletar) para as seguintes entidades:

* **Autenticação**: Registro de usuários (administradores), login e atualização de token JWT.
* **Clientes**: Gerenciamento de informações de clientes, incluindo autenticação própria.
* **Categorias**: Gerenciamento de categorias de produtos.
* **Gêneros**: Gerenciamento de gêneros para os produtos (ex: Masculino, Feminino).
* **Produtos**: Gerenciamento de produtos, incluindo descrição, preço, estoque e associações com tamanho, categoria e gênero.
* **Imagens de Produtos**: Gerenciamento de URLs de imagens associadas aos produtos.
* **Pedidos**: Criação e gerenciamento de pedidos, incluindo itens do pedido e cálculo de subtotal.
* **Tamanhos**: Gerenciamento de tamanhos para os produtos (ex: P, M, G).

## Tecnologias Utilizadas

* **Python 3.x**
* **FastAPI**: Framework web para construção da API.
* **SQLAlchemy**: ORM para interação com o banco de dados.
* **PostgreSQL**: Banco de dados relacional.
* **Alembic**: Ferramenta para gerenciamento de migrações de banco de dados.
* **Pydantic**: Para validação de dados e configurações.
* **Passlib (com bcrypt)**: Para hashing de senhas.
* **python-jose**: Para manipulação de tokens JWT.
* **Uvicorn**: Servidor ASGI para FastAPI.
* **Docker e Docker Compose**: Para containerização e orquestração dos serviços.
* **python-dotenv**: Para gerenciamento de variáveis de ambiente.

## Pré-requisitos

* Python 3.8+
* Docker e Docker Compose (recomendado para facilitar a execução com o banco de dados)
* Poetry (ou Pip para instalar dependências do `requirements.txt`)
* Um arquivo `.env` configurado (veja a seção de Variáveis de Ambiente).

## Configuração do Ambiente

1.  **Clone o repositório:**
    ```bash
    git clone git@github.com:Migguell/infog2.git
    cd infog2
    ```

2.  **Crie e configure o arquivo `.env`:**
    Copie o arquivo `.env.example` para `.env` ou crie um novo `.env` na raiz do projeto com as seguintes variáveis:
    ```env
    DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME
    SECRET_KEY=sua_chave
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30

    # Variáveis para o Docker Compose (se usar)
    POSTGRES_USER=admin
    POSTGRES_PASSWORD=admin
    POSTGRES_DB=infog2_db
    POSTGRES_HOST_PORT=5432
    POSTGRES_CONTAINER_PORT=5432

    # Opcional
    SENTRY_DSN=
    ```
    **Atenção**: Se estiver usando o `docker-compose.yml` fornecido, o `DATABASE_URL` para a aplicação dentro do container Docker deve referenciar o serviço do banco de dados (ex: `postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:${POSTGRES_CONTAINER_PORT}/${POSTGRES_DB}`).

3.  **Instale as dependências:**
    Se não estiver usando Docker, é recomendado usar um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    pip install -r requirements.txt
    ```

## Executando a Aplicação

### Com Docker Compose (Recomendado)

Esta é a forma mais simples de subir a API junto com o banco de dados PostgreSQL.

1.  Certifique-se de que o Docker e Docker Compose estão instalados e em execução.
2.  Na raiz do projeto, execute:
    ```bash
    docker-compose up --build
    ```
    O comando `docker-compose.yml` também aplicará as migrações do Alembic (`alembic upgrade head`) antes de iniciar a API.

A API estará acessível em `http://localhost:8000`.

### Localmente (Sem Docker para a API)

Se você configurou um PostgreSQL separadamente e ajustou o `DATABASE_URL` no seu arquivo `.env` para apontar para ele:

1.  **Aplique as migrações do banco de dados:**
    ```bash
    alembic upgrade head
    ```

2.  **Inicie o servidor Uvicorn:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    A API estará acessível em `http://localhost:8000`.

## Variáveis de Ambiente

As seguintes variáveis de ambiente são usadas para configurar a aplicação:

* `DATABASE_URL`: URL de conexão com o banco de dados PostgreSQL.
* `SECRET_KEY`: Chave secreta para a codificação JWT e outras necessidades de segurança.

Para o `docker-compose.yml`:
* `POSTGRES_USER`: Usuário do banco de dados.
* `POSTGRES_PASSWORD`: Senha do banco de dados.
* `POSTGRES_DB`: Nome do banco de dados.
* `POSTGRES_HOST_PORT`: Porta do host a ser mapeada para a porta do container do PostgreSQL.
* `POSTGRES_CONTAINER_PORT`: Porta interna do container do PostgreSQL.

## Documentação da API

Com a aplicação em execução, a documentação interativa da API estará disponível nos seguintes endpoints:

* **Swagger UI**: `http://localhost:8000/docs`
* **ReDoc**: `http://localhost:8000/redoc`

## Migrações do Banco de Dados (Alembic)

O Alembic é usado para gerenciar as migrações do esquema do banco de dados.

* **Para aplicar as migrações mais recentes:**
    ```bash
    alembic upgrade head
    ```
* **Para criar uma nova migração (após alterações nos modelos SQLAlchemy em `app/database/models.py`):**
    ```bash
    alembic revision -m "migration"
    ```
    Edite o arquivo de migração gerado em `migrations/versions/` para ajustar os comandos de `upgrade` e `downgrade` conforme necessário.

* **Configuração do Alembic:**
    * `alembic.ini`: Arquivo de configuração principal do Alembic.
    * `migrations/env.py`: Script de configuração do ambiente do Alembic, define como as migrações são executadas.