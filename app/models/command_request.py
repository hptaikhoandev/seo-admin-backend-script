from pydantic import BaseModel

class CommandRequest(BaseModel):
    team: str
    server_ip: str
    command: str