from pydantic import BaseModel
from typing import List

class DestroysiteRequest(BaseModel):
    team: str
    server_ip: str
    domains: List[str]