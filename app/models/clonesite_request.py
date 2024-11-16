from pydantic import BaseModel
from typing import List

class ClonesiteRequest(BaseModel):
    team: str
    server_ip: str
    source_domain: str
    target_domain: str