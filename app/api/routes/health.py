from fastapi import APIRouter, HTTPException
from app.config import config
from app.repository.db import BaseRepository
from app.utils.logger import logger

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check():
    """
    Проверка состояния API и подключения к базе данных
    """
    if config.DISABLE_DB_CHECK:
        return {"status": "success", "database": "check_disabled"}

    conn = None
    try:
        conn = BaseRepository.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "success", "database": "connected"}
    except Exception as e:
        logger.error(f"❌ Ошибка проверки состояния БД: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if conn:
            BaseRepository.release_connection(conn)
