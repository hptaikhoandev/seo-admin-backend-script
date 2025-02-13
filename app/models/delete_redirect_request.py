from pydantic import BaseModel
from typing import List

class DeleteRedirectRequest(BaseModel):
    team: str
    redirect_type: str
    source_domains: List[str]
    target_domains: List[str]
    delete_domains: List[str]