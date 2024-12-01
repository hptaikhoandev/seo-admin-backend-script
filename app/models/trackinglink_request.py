from pydantic import BaseModel
from typing import List

class TrackinglinkRequest(BaseModel):
    team: str
    server_ip: str
