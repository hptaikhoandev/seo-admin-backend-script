from pydantic import BaseModel
from typing import List

class RedirectRequest(BaseModel):
    team: str
    redirect_type: str
    source_domains: List[str]
    target_domains: List[str]