from pydantic import BaseModel

class DashboardRequest(BaseModel):
    team: str
    server_ip: str