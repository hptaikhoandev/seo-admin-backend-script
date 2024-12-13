from pydantic import BaseModel
from typing import List
from typing import Optional

class ServerRequest(BaseModel):
    team: str
    server_ip: str
    transitions: Optional[str] = None
