from fastapi import APIRouter, HTTPException
from app.config import config
from app.db.db import init_connection
from app.utils.logger import logger

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check():
    """
    Проверка состояния API и подключения к базе данных
    """
    try:
        if config.DISABLE_DB_CHECK:
            return {"status": "success", "database": "check_disabled"}
        else:
            init_connection()
            return {"status": "success", "database": "connected"}
    except Exception as e:
        logger.error(f"❌ Ошибка проверки состояния: {e}")
        raise HTTPException(status_code=500, detail=str(e))
