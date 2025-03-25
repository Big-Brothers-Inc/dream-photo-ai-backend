from fastapi import APIRouter

router = APIRouter()


@router.get("/train/test")
async def test_train():
    return {"message": "Training route works!"}
