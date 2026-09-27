from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from catalog_api.config import api_config
from catalog_api.routes import router

cfg = api_config()
app = FastAPI(title="Catalog Analytics API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cfg.web_origin],
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)
