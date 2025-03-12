from pydantic import BaseModel

class SubDomainRequest(BaseModel):
    id: str
    dns_id: str
    zone_id: str
    name: str
    content: str
    account_id: str
