from fastapi import FastAPI
from app.routers import item_router
from app.routers import domain_router

app = FastAPI()

# Đăng ký router
app.include_router(item_router.router)
app.include_router(domain_router.router)

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI MVC App"}