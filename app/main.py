from fastapi import FastAPI

app = FastAPI(
    title="Infog2 API",
    description="API RESTful para gerenciar clientes, produtos e pedidos da Lu Estilo.",
    version="1.0.0"
)

@app.get("/")
async def read_root():
    return {"message": "Bem-vindo à Lu Estilo API!"}