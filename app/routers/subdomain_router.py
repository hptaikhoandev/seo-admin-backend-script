from fastapi import APIRouter, HTTPException, FastAPI, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.subdomain_controller import SubDomainController
from app.models.subdomain_request import SubDomainRequest
from app.models.subdomainHistory_request import SubDomaiHistoryRequest


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


@router.post("/script/update-dns-record")
async def get_dns_records(request: SubDomainRequest):
    return await SubDomainController.update_dns_records(request)

@router.get("/script/get-dns-records-by-name")
async def get_domain_info(search: str = Query(...), team: str = Query(...)):
    return await SubDomainController.get_dns_records_by_name(search, team)

@router.post("/script/add-subdomainHistory")
async def create_dns_record(request: SubDomaiHistoryRequest):
    return await SubDomainController.add_subdomainHistory(request)
