from fastapi import APIRouter, HTTPException, FastAPI, Depends, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.command_controller import CommandController
from app.models.command_request import CommandRequest


router = APIRouter()
security = HTTPBearer()
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiaWF0IjoxNzI0NDQzNTM3LCJleHAiOjE3MjQ0ODY3Mzd9.ynCTq1ImUmD4h6ZpZ7EaMy43nvDga8vqUURlPdAZDDI"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )


@router.post("/script/exec-command")
async def execute_command(request: CommandRequest):
    return await CommandController.exec_commands(request)