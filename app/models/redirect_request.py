from pydantic import BaseModel
from typing import List

class RedirectRequest(BaseModel):
    http_code: str
    new_domain: str
    domains: List[str]