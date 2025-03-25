from fastapi import FastAPI
from .train import router as train_router
from .health import router as health_router
from .root import router as root_router


def register_all_routes(app: FastAPI):
    app.include_router(train_router, prefix="/train")
    app.include_router(health_router)
    app.include_router(root_router)
