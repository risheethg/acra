import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from ..core.config import settings


# NO TOOL IMPORT NEEDED

def run_code_analysis_crew(pr_diff: str) -> str:
    """
    Initializes and runs the code analysis crew with a provided PR diff.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini/gemini-1.5-flash-latest",
        verbose=True,
        temperature=0.1,
        google_api_key=settings.GOOGLE_API_KEY
    )

    # The agent no longer needs any tools.
    code_reviewer_agent = Agent(
        role='Senior Software Engineer and Code Review Specialist',
        goal="""Analyze a provided code diff to identify code style issues,
        potential bugs, performance improvements, and adherence to best practices.""",
        backstory="""You are an expert software engineer with a meticulous eye for detail.
        You are given a code diff and must provide a structured analysis in a clean JSON format.""",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

    # The task now takes the diff directly in its description.
    code_analysis_task = Task(
        description=f"""Analyze the following code diff and provide a structured review.
        The diff shows changes in a pull request. Your analysis should cover:
        1.  **Code Style & Formatting**: Inconsistencies and style guide violations.
        2.  **Potential Bugs**: Logical errors, null pointer risks, etc.
        3.  **Performance**: Suggestions for inefficient code.
        4.  **Best Practices**: Adherence to language and general programming best practices.

        Your final output **MUST** be a single, clean JSON object matching this exact structure:
        {{
            "files": [{{ "name": "path/to/file.py", "issues": [{{ "type": "bug", "line": 42, "description": "...", "suggestion": "..." }}] }}],
            "summary": {{ "total_files": 1, "total_issues": 1, "critical_issues": 0 }}
        }}
        Do not include any markdown formatting or any text outside of this JSON structure.

        Here is the code diff to analyze:
        ---
        {pr_diff}
        ---
        """,
        expected_output="A single, raw JSON object containing the structured code review analysis.",
        agent=code_reviewer_agent
    )

    review_crew = Crew(
        agents=[code_reviewer_agent],
        tasks=[code_analysis_task],
        process=Process.sequential,
        verbose=True
    )

    # The kickoff is now much simpler as no inputs are needed for tools.
    result = review_crew.kickoff()
    return result

