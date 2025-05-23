from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.clients.routes import router as clients_router
from app.category.routes import router as categories_router
from app.gender.routes import router as genders_router
from app.product.routes import router as products_router
from app.product_image.routes import router as product_images_router
from app.purchase.routes import router as purchases_router
from app.size.routes import router as sizes_router

app = FastAPI(
    title="Infog2 API",
    description="API RESTful para gerenciar clientes, produtos e pedidos da Lu Estilo.",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(categories_router)
app.include_router(genders_router)
app.include_router(products_router)
app.include_router(product_images_router)
app.include_router(purchases_router)
app.include_router(sizes_router)

@app.get("/")
async def read_root():
    return {"message": "Bem-vindo à Lu Estilo API!"}