from pydantic import BaseModel
from typing import List

class MultisiteRequest(BaseModel):
    team: str
    server_ip: str
    domains: List[str]