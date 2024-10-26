from fastapi import APIRouter, HTTPException
from app.controllers.domain_controller import DomainController
from app.models.domain_request import DomainRequest

router = APIRouter()

@router.post("/script/add-list-domains-to-cloudflare")
async def add_domains(request: DomainRequest):
    return await DomainController.add_domains(request)

