from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import item_router
from app.routers import domain_router
from app.routers import redirect_router
from app.routers import clonesite_router
from app.routers import multisite_router
from app.routers import admin_router
from app.routers import dashboard_router
from app.routers import destroysite_router
from app.routers import tracking_link_router
from dotenv import load_dotenv
import os

app = FastAPI()

# Xóa cache của các biến môi trường
def reload_env():
    for key in list(os.environ.keys()):
        if key not in os.environ._data:
            del os.environ[key]
    load_dotenv()

# Tải biến môi trường khi ứng dụng khởi động
reload_env()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
# Đăng ký router
app.include_router(item_router.router)
app.include_router(domain_router.router)
app.include_router(redirect_router.router)
app.include_router(clonesite_router.router)
app.include_router(multisite_router.router)
app.include_router(destroysite_router.router)
app.include_router(admin_router.router)
app.include_router(dashboard_router.router)
app.include_router(tracking_link_router.router)

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI MVC App"}