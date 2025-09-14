from fastapi import FastAPI
from app.routes import analysis
from app.core.logging import setup_logging

# Setup structured logging
setup_logging()

app = FastAPI(
    title="Autonomous Code Review Agent API",
    description="An API for an AI-powered code review agent that analyzes GitHub pull requests.",
    version="0.1.0",
)

app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])