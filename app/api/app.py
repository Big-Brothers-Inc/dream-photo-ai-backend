from fastapi import FastAPI
from app.config import config
from app.api.lifecycle import setup_lifecycle
from app.api.middlewares import setup_middlewares


app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    contact={
        "name": config.API_CONTACT_NAME,
        "email": config.API_CONTACT_EMAIL,
        "url": config.API_CONTACT_URL,
    },
    docs_url=config.DOCS_URL,
    redoc_url=config.REDOC_URL,
    openapi_url=config.OPENAPI_URL,
)

setup_lifecycle(app)
setup_middlewares(app)
