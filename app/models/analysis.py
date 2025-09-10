from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class PRAnalysisRequest(BaseModel):
    """
    Request model for the /analyze-pr endpoint.
    """
    repo_url: HttpUrl = Field(..., example="https://github.com/user/repo")
    pr_number: int = Field(..., example=123)
    github_token: Optional[str] = Field(None, example="ghp_...")

class TaskStatusResponse(BaseModel):
    """
    Response model for the status endpoint.
    """
    task_id: str
    status: str
    detail: Optional[str] = None

# --- Nested Models for the Result ---

class Issue(BaseModel):
    """
    Represents a single issue found in a file.
    """
    type: str = Field(..., example="bug")
    line: int = Field(..., example=42)
    description: str = Field(..., example="Potential null pointer dereference.")
    suggestion: str = Field(..., example="Add a null check before accessing the object.")

class FileAnalysis(BaseModel):
    """
    Contains the analysis results for a single file.
    """
    name: str = Field(..., example="src/main.py")
    issues: List[Issue]

class AnalysisSummary(BaseModel):
    """
    A high-level summary of the analysis results.
    """
    total_files: int = Field(..., example=5)
    total_issues: int = Field(..., example=10)
    critical_issues: int = Field(..., example=2)

class AnalysisResultData(BaseModel):
    """
    The main data structure for the analysis results.
    """
    files: List[FileAnalysis]
    summary: AnalysisSummary

class TaskResultResponse(BaseModel):
    """
    Response model for the results endpoint.
    """
    task_id: str
    status: str
    results: AnalysisResultData

