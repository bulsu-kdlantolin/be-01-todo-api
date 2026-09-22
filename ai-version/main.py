from typing import Dict, List, Optional
from fastapi import FastAPI, Path, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Pydantic Models for Validation
# ---------------------------------------------------------------------------
class TaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The title of the task (1-100 characters).",
        examples=["Buy groceries"],
    )
    done: bool = Field(
        default=False,
        description="Whether the task has been completed.",
        examples=[False],
    )


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated title of the task (optional).",
        examples=["Buy groceries & cook dinner"],
    )
    done: Optional[bool] = Field(
        default=None,
        description="Updated completion status (optional).",
        examples=[True],
    )


class TaskResponse(TaskBase):
    id: int = Field(..., description="Unique integer identifier for the task.")


# ---------------------------------------------------------------------------
# 2. FastAPI Application Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ToDo CRUD API",
    description="A simple in-memory CRUD ToDo API built with FastAPI and Pydantic.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# 3. Custom Validation Error Handler (422 Unprocessable Entity)
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Formats validation errors into a clean, customized JSON response."""
    errors = [
        {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation failed on the submitted data.",
            "errors": errors,
        },
    )


# ---------------------------------------------------------------------------
# 4. In-Memory Database / Seed Data
# ---------------------------------------------------------------------------
tasks_db: Dict[int, dict] = {
    1: {"id": 1, "title": "Set up project repository", "done": True},
    2: {"id": 2, "title": "Design FastAPI CRUD endpoints", "done": True},
    3: {"id": 3, "title": "Write comprehensive unit tests", "done": False},
}


# ---------------------------------------------------------------------------
# 5. API Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Returns the operational status of the service.",
    status_code=status.HTTP_200_OK,
)
def get_health():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "message": "Service is healthy and operational."},
    )


@app.get(
    "/tasks",
    tags=["Tasks"],
    summary="Retrieve all tasks",
    description="Fetches a list of all existing tasks in the database.",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_tasks():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=list(tasks_db.values()),
    )


@app.get(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Retrieve task by ID",
    description="Fetches a single task by its unique ID. Returns 404 if not found.",
    response_model=TaskResponse,
)
def get_task_by_id(
    task_id: int = Path(..., gt=0, description="The ID of the task to retrieve.")
):
    task = tasks_db.get(task_id)
    if not task:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": f"Task with ID {task_id} was not found.",
            },
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=task)


@app.post(
    "/tasks",
    tags=["Tasks"],
    summary="Create a new task",
    description="Creates a new task with an auto-incremented ID and saves it to the database.",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(payload: TaskCreate):
    # Ensure title is not just whitespace
    if not payload.title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": "Title cannot be empty or solely whitespace.",
            },
        )

    # Generate new ID (auto-increment)
    new_id = max(tasks_db.keys(), default=0) + 1
    new_task = {"id": new_id, "title": payload.title.strip(), "done": payload.done}
    tasks_db[new_id] = new_task

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_task)


@app.put(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Update a task",
    description="Updates one or more fields of an existing task. Returns 404 if not found or 400 if no update fields are provided.",
    response_model=TaskResponse,
)
def update_task(
    payload: TaskUpdate,
    task_id: int = Path(..., gt=0, description="The ID of the task to update."),
):
    if task_id not in tasks_db:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": f"Task with ID {task_id} was not found.",
            },
        )

    # Ensure at least one field was sent in the body
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": "No update fields were provided. Specify at least 'title' or 'done'.",
            },
        )

    # Check for empty whitespace-only title if title is being updated
    if "title" in update_data:
        cleaned_title = update_data["title"].strip()
        if not cleaned_title:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Title cannot be empty or solely whitespace.",
                },
            )
        update_data["title"] = cleaned_title

    tasks_db[task_id].update(update_data)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=tasks_db[task_id],
    )


@app.delete(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Delete a task",
    description="Deletes a task by ID. Returns 404 if the task is not found.",
)
def delete_task(
    task_id: int = Path(..., gt=0, description="The ID of the task to delete.")
):
    if task_id not in tasks_db:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": f"Task with ID {task_id} was not found.",
            },
        )

    deleted_task = tasks_db.pop(task_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": f"Task {task_id} has been deleted successfully.",
            "deleted_task": deleted_task,
        },
    )


# ---------------------------------------------------------------------------
# 6. Server Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)