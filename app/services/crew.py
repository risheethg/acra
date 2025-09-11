import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

from .agent_tools import GetPRDiffTool
from ..core.config import settings

def run_code_analysis_crew(repo_url: str, pr_number: int, github_token: str = None) -> str:
    """
    Initializes and runs the code analysis crew with Gemini.
    """
    # Initialize the Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        verbose=True,
        temperature=0.1,
        google_api_key=settings.GEMINI_API_KEY
    )

    # Initialize the custom tool for fetching PR diffs
    pr_diff_tool = GetPRDiffTool()

    # Define the Code Review Agent
    code_reviewer_agent = Agent(
        role='Senior Software Engineer and Code Review Specialist',
        goal="""Analyze a GitHub pull request diff to identify code style issues,
        potential bugs, performance improvements, and adherence to best practices.""",
        backstory="""You are an expert software engineer with decades of experience in multiple programming
        languages and a meticulous eye for detail. You are tasked with reviewing code to ensure it meets
        the highest standards of quality, readability, and performance.""",
        verbose=True,
        llm=llm,
        tools=[pr_diff_tool],
        allow_delegation=False
    )

    # Define the Code Analysis Task
    code_analysis_task = Task(
        description=f"""Analyze the code changes in the pull request diff for repository '{repo_url}' at PR number {pr_number}.
        Your analysis should cover:
        1.  **Code Style & Formatting**: Check for inconsistencies and style guide violations.
        2.  **Potential Bugs**: Identify logical errors, null pointer risks, or other potential bugs.
        3.  **Performance**: Suggest optimizations for inefficient code.
        4.  **Best Practices**: Ensure the code follows language-specific and general programming best practices.

        Your final output **MUST** be a single, clean JSON object matching this exact structure:
        {{
            "files": [{{ "name": "path/to/file.py", "issues": [{{ "type": "bug", "line": 42, "description": "...", "suggestion": "..." }}] }}],
            "summary": {{ "total_files": 1, "total_issues": 1, "critical_issues": 0 }}
        }}
        Do not include any markdown formatting like ```json or any text outside of this JSON structure.
        """,
        expected_output="A single, raw JSON object containing the structured code review analysis.",
        agent=code_reviewer_agent,
        inputs={'repo_url': repo_url, 'pr_number': pr_number, 'github_token': github_token}
    )

    # Assemble and run the Crew
    review_crew = Crew(
        agents=[code_reviewer_agent],
        tasks=[code_analysis_task],
        process=Process.sequential,
        verbose=2
    )

    result = review_crew.kickoff()
    return result