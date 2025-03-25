from fastapi import Request
from app.utils.logger import logger


def setup_middlewares(app):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        return response
