from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["System"])
async def root():
    return {"status": "ok", "message": "Dream Photo API is running"}
