from pydantic import BaseModel
from typing import List

class DeleteRedirectRequest(BaseModel):
    team: str
    domains: List[str]