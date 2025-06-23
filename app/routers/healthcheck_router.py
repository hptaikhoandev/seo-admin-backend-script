from fastapi import APIRouter

router = APIRouter()

@router.get("/script/health-check")
async def health_check():
    return {
        "status": "healthy"
    }
