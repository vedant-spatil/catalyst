from catalog_api.config import api_config
from catalog_api.main import app
import os
import uvicorn

if __name__ == "__main__":
    cfg = api_config()
    host = os.environ.get("API_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=cfg.api_port)
