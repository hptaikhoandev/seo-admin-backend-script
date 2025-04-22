from pydantic import BaseModel
from typing import List

class MigratesiteRequest(BaseModel):
    team: str
    source_ip: str
    target_ip: str
    source_domain: str