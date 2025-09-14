import logging
from fastapi import APIRouter, HTTPException, status, Body
from celery.result import AsyncResult
from typing import Dict, Any

from ..models.analysis import PRAnalysisRequest, TaskStatusResponse, TaskResultResponse
from ..core.celery_app import celery_app
from app.services.tasks import run_code_analysis_task

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache for completed task results. For production, use a distributed cache like Redis.
results_cache: Dict[str, Any] = {}

@router.post("/analyze-pr", status_code=status.HTTP_202_ACCEPTED, response_model=TaskStatusResponse)
async def analyze_pr(request: PRAnalysisRequest = Body(...)):
    """Accepts GitHub PR details and queues the analysis."""
    logger.info(f"Received analysis request for {request.repo_url} PR #{request.pr_number}")
    task = run_code_analysis_task.delay(str(request.repo_url), request.pr_number, request.github_token)
    logger.info(f"Task {task.id} queued for analysis.")
    return {"task_id": task.id, "status": "PENDING"}


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Checks the status of an analysis task."""
    logger.info(f"Checking status for task {task_id}")
    task_result = AsyncResult(task_id, app=celery_app)
    task_status = task_result.state
    detail = None

    if task_status == 'PROCESSING':
        detail = task_result.info.get('status', 'The task is currently being processed.')
    elif task_status == 'FAILURE':
        # Safely access error information
        result = task_result.result
        if isinstance(result, Exception):
            detail = f"Task failed with an error: {result}"
        else:
            detail = "Task failed with an unknown error."
        logger.error(f"Task {task_id} failed: {detail}")

    return {"task_id": task_id, "status": task_status, "detail": detail}


@router.get("/results/{task_id}", response_model=TaskResultResponse)
async def get_task_results(task_id: str):
    """Retrieves the results of a completed analysis task."""
    logger.info(f"Fetching results for task {task_id}")

    # Check our in-memory cache first
    if task_id in results_cache:
        logger.info(f"Returning cached result for task {task_id}")
        return results_cache[task_id]

    # If not in cache, check with the Celery backend
    task_result = AsyncResult(task_id, app=celery_app)

    if not task_result.ready():
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Task is not complete. Current status: {task_result.state}"
        )

    if task_result.failed():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task failed. Use the status endpoint for more details."
        )

    # Task succeeded, prepare the response
    response_data = {
        "task_id": task_id,
        "status": "COMPLETED",
        "results": task_result.get()
    }
    
    # Store the successful result in the cache
    results_cache[task_id] = response_data
    logger.info(f"Result for task {task_id} cached.")

    return response_data
