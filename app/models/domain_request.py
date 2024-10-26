from pydantic import BaseModel
from typing import List

class DomainRequest(BaseModel):
    server_ip: str
    ssl_type: str
    domains: List[str]