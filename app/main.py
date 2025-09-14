from fastapi import FastAPI
from .routes import analysis
from .core.logging import setup_logging

# Set up logging as soon as the application starts
setup_logging()

app = FastAPI(
    title="Autonomous Code Review Agent API",
    description="An API for an AI-powered code review agent that analyzes GitHub pull requests.",
    version="0.1.0",
)

# Include the API router
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

@app.get("/", tags=["root"])
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Code Review Agent API is running."}

