import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

from ..core.config import settings

class Issue(BaseModel):
    """Represents a single issue found in a file."""
    type: str = Field(..., description="The type of issue (e.g., 'bug', 'style', 'performance', 'best-practice').")
    line: int = Field(..., description="The line number where the issue occurs.")
    description: str = Field(..., description="A detailed description of the issue.")
    suggestion: str = Field(..., description="A concrete suggestion for how to fix the issue.")

class FileAnalysis(BaseModel):
    """Contains the analysis results for a single file."""
    name: str = Field(..., description="The full path of the file being analyzed.")
    issues: List[Issue] = Field(..., description="A list of issues found in the file.")

class AnalysisSummary(BaseModel):
    """A high-level summary of the analysis results."""
    total_files: int = Field(..., description="The total number of files analyzed.")
    total_issues: int = Field(..., description="The total number of issues found across all files.")
    critical_issues: int = Field(..., description="The number of issues classified as critical bugs.")

class AnalysisResultData(BaseModel):
    """The main data structure for the analysis results, matching the required JSON output."""
    files: List[FileAnalysis]
    summary: AnalysisSummary

def analyze_code_with_langchain(pr_diff: str) -> str:
    """
    Analyzes a PR diff using a direct LangChain chain with Google Gemini
    and returns a structured JSON string.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=settings.GOOGLE_API_KEY
    )

    # The prompt provides the LLM with a role and the task.
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert Senior Software Engineer with a meticulous eye for detail.
            Your task is to analyze a provided code diff and provide a structured analysis.
            Identify code style issues, potential bugs, performance improvements,
            and adherence to best practices. Your output must be a valid JSON object.
            """
        ),
        (
            "human",
            """Please analyze the following code diff and provide your review.

            Here is the code diff to analyze:
            ---
            {pr_diff}
            ---
            """
        )
    ])

    # Create a chain that forces the LLM to return a JSON object matching the AnalysisResultData model.
    structured_llm = llm.with_structured_output(AnalysisResultData)
    chain = prompt | structured_llm

    # Invoke the chain with the PR diff.
    result_object = chain.invoke({"pr_diff": pr_diff})

    FILTER_STRING = "Missing newline at the end of the file"

    # Create a new list of files, filtering issues within each file
    filtered_files = []
    for file_analysis in result_object.files:
        # Use a list comprehension to keep only the issues that DON'T match the filter string
        filtered_issues = [
            issue for issue in file_analysis.issues 
            if FILTER_STRING not in issue.description
        ]
        
        # If the file still has issues after filtering, add it to our new list
        if filtered_issues:
            file_analysis.issues = filtered_issues
            filtered_files.append(file_analysis)

    # Replace the original files list with the filtered one
    result_object.files = filtered_files

    # Recalculate the summary based on the filtered results
    total_issues = sum(len(file.issues) for file in result_object.files)
    critical_issues = sum(
        1 for file in result_object.files 
        for issue in file.issues if issue.type.lower() == 'bug'
    )
    result_object.summary.total_files = len(result_object.files)
    result_object.summary.total_issues = total_issues
    result_object.summary.critical_issues = critical_issues

    # Return the Pydantic model as a JSON string.
    return result_object.json()