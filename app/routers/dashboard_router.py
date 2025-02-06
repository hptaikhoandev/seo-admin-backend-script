from fastapi import APIRouter, HTTPException, FastAPI, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.dashboard_controller import DashboardController
from app.models.dashboard_request import DashboardRequest

router = APIRouter()
security = HTTPBearer()
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiaWF0IjoxNzI0NDQzNTM3LCJleHAiOjE3MjQ0ODY3Mzd9.ynCTq1ImUmD4h6ZpZ7EaMy43nvDga8vqUURlPdAZDDI"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

@router.get("/script/count-domains")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def count_domains(server_ip: str = Query(...), team: str = Query(...)):
    return await DashboardController.count_domains(server_ip, team)

@router.get("/script/param-dashboard")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def param_dashboard(server_ip: str = Query(...), team: str = Query(...)):
    return await DashboardController.param_dashboard(server_ip, team)


@router.get("/script/param-dashboard-ssh")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def param_dashboard_ssh(server_ip: str = Query(...), team: str = Query(...), username: str = Query(...), private_key: str = Query(...)):
    return await DashboardController.param_dashboard_ssh(server_ip, team, username, private_key)
