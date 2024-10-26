from pydantic import BaseModel
from typing import List

class DomainRequest(BaseModel):
    team: str
    server_ip: str
    ssl_type: str
    domains: List[str]