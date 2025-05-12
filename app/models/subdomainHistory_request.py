from pydantic import BaseModel

class SubDomaiHistoryRequest(BaseModel):
    dns_id: str
    zone_id: str
    type: str
    name: str
    content: str
    account_id: str
    team: str
