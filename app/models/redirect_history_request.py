from pydantic import BaseModel
from typing import List

class RedirectHistoryRequest(BaseModel):
    team: str
    domains: str


class DeleteredirectHistoryRequest(BaseModel):
    team: str
    zone_id: str
    rule_id: str