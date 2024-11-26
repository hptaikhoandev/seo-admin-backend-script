from pydantic import BaseModel
from typing import List

class ServerRequest(BaseModel):
    team: str
    server_ip: str
