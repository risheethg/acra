from fastapi import FastAPI
from app.routes import analysis
from app.core.logging import setup_logging

# Setup structured logging
setup_logging()

app = FastAPI(title="Autonomous Code Review Agent")

app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])