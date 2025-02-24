from fastapi import APIRouter, HTTPException, FastAPI, Depends, status, Body, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.redirect_controller import RedirectController
from app.models.redirect_request import RedirectRequest
from app.models.delete_redirect_request import DeleteRedirectRequest
from app.models.redirect_history_request import RedirectHistoryRequest


router = APIRouter()
security = HTTPBearer()
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiaWF0IjoxNzI0NDQzNTM3LCJleHAiOjE3MjQ0ODY3Mzd9.ynCTq1ImUmD4h6ZpZ7EaMy43nvDga8vqUURlPdAZDDI"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

@router.post("/script/redirect-domains")
# async def add_domains(request: DomainRequest, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
async def redirect_domains(request: RedirectRequest):
    return await RedirectController.create_redirect(request)

@router.delete("/script/redirect-domains")
async def delete_redirect_domains(request: DeleteRedirectRequest = Body(...)):
    return await RedirectController.delete_redirect(request)


@router.get("/script/get-rules-from-domains")
async def redirect_history(team: str, domains: str = Query(...)):
    domain_list = [domain.strip() for domain in domains.split(',')]
    return await RedirectController.redirect_history(team, domain_list)