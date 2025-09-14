# You can rename this file to something like app/services/analyzer.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

from ..core.config import settings

# Step 1: Define the desired JSON output structure using Pydantic
# This is the same structure you defined in your prompt and models/analysis.py
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

# This function REPLACES run_code_analysis_crew
def analyze_code_with_langchain(pr_diff: str) -> str:
    """
    Analyzes a PR diff using a direct LangChain chain with Google Gemini
    and returns a structured JSON string.
    """
    # Step 2: Set up the LLM, just like before.
    # NOTE: Because we are using the official Google library directly, the model name
    # does NOT need the 'gemini/' prefix.
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        temperature=0.1,
        google_api_key=settings.GOOGLE_API_KEY
    )

    # Step 3: Create a prompt template that combines the persona and the task.
    # The persona (backstory, role, goal) becomes the "system" message.
    # The specific request (the diff) becomes the "human" message.
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert Senior Software Engineer with a meticulous eye for detail.
            Your task is to analyze a provided code diff and provide a structured analysis.
            Your analysis must identify code style issues, potential bugs, performance improvements,
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

    # Step 4: Create the chain and bind it to the structured output model.
    # This is the magic part: `.with_structured_output()` forces the LLM
    # to return a JSON object that matches our `AnalysisResultData` model.
    structured_llm = llm.with_structured_output(AnalysisResultData)
    chain = prompt | structured_llm

    # Step 5: Invoke the chain with the PR diff
    result_object = chain.invoke({"pr_diff": pr_diff})

    # Step 6: Return the result as a JSON string
    return result_object.json()