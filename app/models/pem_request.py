from pydantic import BaseModel
from typing import List

class PemRequest(BaseModel):
    team: str
