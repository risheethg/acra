# Autonomous Code Review Agent

This project is an autonomous code review agent system that uses AI to analyze GitHub pull requests. The system implements a goal-oriented AI agent that can plan and execute code reviews independently, process them asynchronously using Celery, and interact with developers through a structured API.

It is built with Python, FastAPI, Celery, Redis, and uses the Google Gemini API via LangChain for its AI analysis capabilities.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Technical Stack](#technical-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Local Installation](#local-installation)
  - [Running with Docker](#running-with-docker)
- [API Documentation](#api-documentation)
  - [1. Analyze a Pull Request](#1-analyze-a-pull-request)
  - [2. Check Task Status](#2-check-task-status)
  - [3. Retrieve Task Results](#3-retrieve-task-results)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)

## Features

- **Asynchronous Code Analysis**: Leverages Celery and Redis to handle long-running code review tasks without blocking the API.
- **AI-Powered Reviews**: Uses Google's Gemini model via LangChain to provide insightful code reviews, identifying bugs, style issues, and best practice violations.
- **Structured JSON Output**: The AI is prompted to return a structured JSON object, ensuring predictable and parsable review results.
- **Status & Result Endpoints**: Provides API endpoints to track the progress of an analysis and retrieve the final, structured results.
- **Result Caching**: Implements a basic in-memory cache for completed task results to reduce load on the Celery backend.
- **Structured Logging**: Configured for clear and informative logs, crucial for debugging and monitoring.
- **Language Agnostic**: The agent analyzes `diff` files, allowing it to review code from any programming language.
- **Comprehensive Testing**: Includes a suite of `pytest` tests for API endpoints and Celery tasks.
- **Containerized & Deployable**: Includes a `Dockerfile` for building the application and a `render.yaml` for easy deployment to Render.

## Project Structure

```
├── app/
│   ├── core/                 # Core components (config, celery, logging)
│   ├── models/               # Pydantic models for API requests/responses
│   ├── routes/               # FastAPI API endpoint definitions
│   ├── services/             # Business logic (AI analysis, GitHub interaction, Celery tasks)
│   └── tests/                # Pytest tests for the application
├── .env.example              # Example environment variables
├── Dockerfile                # Docker configuration for the application
├── render.yaml               # Deployment configuration for Render
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Technical Stack

- **Backend Framework**: FastAPI
- **Asynchronous Tasks**: Celery
- **Message Broker & Cache**: Redis
- **AI/LLM Integration**: LangChain with Google Gemini
- **Testing**: Pytest
- **Containerization**: Docker

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized setup)
- Access to a Redis instance
- A Google Gemini API Key

### Environment Setup

1.  Create a `.env` file in the root directory by copying the example:
    ```bash
    cp .env.example .env
    ```

2.  Fill in the required values in your new `.env` file:
    ```ini
    # URL for your Redis instance
    REDIS_URL="redis://localhost:6379/0"

    # Your Google API Key for Gemini
    GOOGLE_API_KEY="your_google_api_key_here"

    # Optional: A GitHub token to avoid rate-limiting on public repos
    # and to access private repos.
    GITHUB_ACCESS_TOKEN="your_github_personal_access_token"
    ```

### Local Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start Redis**:
    Ensure you have a Redis server running. If using Docker:
    ```bash
    docker run -d -p 6379:6379 redis
    ```

3.  **Start the Celery Worker**:
    In a new terminal, navigate to the project root and run:
    ```bash
    celery -A app.core.celery_app:celery_app worker --loglevel=info
    ```

4.  **Start the FastAPI Server**:
    In another terminal, run:
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

### Running with Docker

A `docker-compose.yml` is the recommended way to run all services together.

1.  Ensure your `.env` file is configured correctly, especially `REDIS_URL=redis://redis:6379/0`. Use `.env.template` as a guide.

2.  Build and run the services:
    ```bash
    docker-compose up --build
    ```

## API Documentation

The API documentation is also available interactively at `http://127.0.0.1:8000/docs` when the server is running.

### 1. Analyze a Pull Request

Queues a new pull request for analysis.

- **Endpoint**: `POST /api/v1/analyze-pr`
- **Request Body**:
  ```json
  {
    "repo_url": "https://github.com/user/repo",
    "pr_number": 123,
    "github_token": "optional_github_token"
  }
  ```
- **Success Response** (`202 Accepted`):
  ```json
  {
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "status": "PENDING"
  }
  ```

### 2. Check Task Status

Checks the current status of an analysis task.

- **Endpoint**: `GET /api/v1/status/{task_id}`
- **Success Response** (`200 OK`):
  ```json
  {
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "status": "PROCESSING",
    "detail": "PR diff fetched. Starting AI analysis..."
  }
  ```
  Possible statuses: `PENDING`, `PROCESSING`, `SUCCESS`, `FAILURE`.

### 3. Retrieve Task Results

Retrieves the final analysis results for a completed task.

- **Endpoint**: `GET /api/v1/results/{task_id}`
- **Success Response** (`200 OK`):
  ```json
  {
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "status": "COMPLETED",
    "results": {
      "files": [
        {
          "name": "path/to/file.py",
          "issues": [
            {
              "type": "bug",
              "line": 42,
              "description": "Potential for null reference exception.",
              "suggestion": "Add a null check before accessing the object."
            }
          ]
        }
      ],
      "summary": {
        "total_files": 1,
        "total_issues": 1,
        "critical_issues": 1
      }
    }
  }
  ```
- **Error Responses**:
  - `202 Accepted`: If the task is not yet complete.
  - `500 Internal Server Error`: If the task failed.

## Running Tests

The project uses `pytest` for testing. The tests are configured to run synchronously without needing a live Redis server.

```bash
pytest
```
