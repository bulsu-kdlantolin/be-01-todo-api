from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from fastapi import Response

app = FastAPI()
tasks = [
    {
        "id": 1, 
        "title": "Task 1", 
        "done": False
    },
    {
        "id": 2, 
        "title": "Task 2",
        "done": True
    },
    {
        "id": 3, 
        "title": "Task 3",
        "done": False
    }
]

class Task(BaseModel):
    title: str 
    done: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/", description="Get API information")
def home():
    return { 
        "name": "Task API", 
        "version": "1.0", 
        "endpoints": ["/tasks"] 
    }

@app.get("/health", description="Check the health of the API")
def health():
    return {
        "status": "ok"
    }

@app.get("/tasks", description="Get all tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}", description="Get a task by ID")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(
        status_code=404, 
        content={"error": f"Task {task_id} not found"}
    )

@app.post("/tasks", description="Create a new task")
def create_task(task: Task):
    if not task.title:
        return JSONResponse(
            status_code=400, 
            content={"error": "Title is missing"}
        )
    
    new_task = {
        "id": max(t["id"] for t in tasks) + 1 if tasks else 1,
        "title": task.title,
        "done": False
    }
    tasks.append(new_task)
    return JSONResponse(status_code=201, content=new_task)

@app.put("/tasks/{task_id}", description="Update a task by ID")
def update_task(task_id: int, task: TaskUpdate):
    if task.title is None and task.done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "No valid fields provided to update"}
        )
    if task.title is not None and task.title == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )
    for existing_task in tasks:
        if existing_task["id"] == task_id:
            if task.title is not None:
                existing_task["title"] = task.title
            if task.done is not None:
                existing_task["done"] = task.done
            return existing_task
        
    return JSONResponse(
        status_code=404, 
        content={"error": f"Task {task_id} not found"}
    )

@app.delete("/tasks/{task_id}", description="Delete a task by ID")
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[i]
            return Response(status_code=204)
    return JSONResponse(
        status_code=404, 
        content={"error": f"Task {task_id} not found"}
    )