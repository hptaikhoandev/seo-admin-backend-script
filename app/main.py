from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import item_router
from app.routers import domain_router
from app.routers import redirect_router
from app.routers import clonesite_router
from app.routers import multisite_router


app = FastAPI()

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

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI MVC App"}