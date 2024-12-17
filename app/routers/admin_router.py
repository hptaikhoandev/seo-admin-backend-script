from fastapi import APIRouter, HTTPException, FastAPI, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.admin_controller import AdminController
from app.models.server_request import ServerRequest

router = APIRouter()
security = HTTPBearer()
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiaWF0IjoxNzI0NDQzNTM3LCJleHAiOjE3MjQ0ODY3Mzd9.ynCTq1ImUmD4h6ZpZ7EaMy43nvDga8vqUURlPdAZDDI"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

@router.post("/script/add-server-domains")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def add_server_domains(request: ServerRequest):
    return await AdminController.add_server_domains(request)

@router.post("/script/status-servers")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def status_servers(request: ServerRequest):
    return await AdminController.status_servers(request)

@router.post("/script/transitions-server")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def transitions_server(request: ServerRequest):
    return await AdminController.transitions_server(request)
