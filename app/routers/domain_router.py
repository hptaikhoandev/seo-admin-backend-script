from fastapi import APIRouter, HTTPException, FastAPI, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.domain_controller import DomainController
from app.models.domain_request import DomainRequest


router = APIRouter()
security = HTTPBearer()
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiaWF0IjoxNzI0NDQzNTM3LCJleHAiOjE3MjQ0ODY3Mzd9.ynCTq1ImUmD4h6ZpZ7EaMy43nvDga8vqUURlPdAZDDI"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

@router.post("/script/add-list-domains-to-cloudflare")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def add_domains(request: DomainRequest):
    return await DomainController.add_domains(request)

