from pydantic import BaseModel

class SubDomainRequest(BaseModel):
    server_ip_list: str