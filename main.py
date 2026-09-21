from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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

@app.get("/")
def home():
    return { 
        "name": "Task API", 
        "version": "1.0", 
        "endpoints": ["/tasks"] 
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.post("/tasks")
def create_task(task: Task):
    if not task.title:
        return JSONResponse(status_code=400, content={"error": "Title is missing"})
    
    new_task = {
        "id": max(task["id"] for task in tasks) + 1 if tasks else 1,
        "title": task.title,
        "done": False
    }
    tasks.append(new_task)
    return JSONResponse(status_code=201, content=new_task)