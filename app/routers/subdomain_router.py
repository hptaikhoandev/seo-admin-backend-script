from fastapi import APIRouter, HTTPException, FastAPI, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.subdomain_controller import SubDomainController
from app.models.subdomain_request import SubDomainRequest


router = APIRouter()
security = HTTPBearer()
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiaWF0IjoxNzI0NDQzNTM3LCJleHAiOjE3MjQ0ODY3Mzd9.ynCTq1ImUmD4h6ZpZ7EaMy43nvDga8vqUURlPdAZDDI"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

@router.get("/script/get-dns-records")
async def get_dns_records(server_ip_list: str = Query(...), page: int = Query(...), per_page: int = Query(...)):
    return await SubDomainController.get_dns_records(server_ip_list, page, per_page)


@router.get("/script/get-ns-dns-records")
async def get_dns_records(search: str = Query(...), page: int = Query(...), limit: int = Query(...), team: str = Query(...)):
    return await SubDomainController.get_ns_dns_records(search, page, limit, team)


