from pydantic import BaseModel
from typing import List

class RedirectHistoryRequest(BaseModel):
    team: str
    domains: str