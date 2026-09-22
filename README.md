# Todo API

A simple CRUD API built with Python and FastAPI (Uvicorn). Built stage by
stage, paying attention to edge cases such as empty versus missing fields and
status codes that did not match the specification.

## Setup and run

Requires Python 3.10 or later.

1. Clone the repository and enter the project folder:

   ```bash
   git clone <your-repo-url>
   cd be-01-todo-api
   ```

2. Create and activate a virtual environment:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:

   ```bash
   uvicorn main:app --reload
   ```

5. Open [`http://localhost:8000/docs`](http://localhost:8000/docs) for the
   interactive Swagger UI, or visit
   [`http://localhost:8000/tasks`](http://localhost:8000/tasks) directly.

## Endpoints

| Method | Endpoint | Description | Success code | Error codes |
| --- | --- | --- | ---: | --- |
| `GET` | `/` | Get API information and available endpoints | `200` | - |
| `GET` | `/health` | Check the health status of the API | `200` | - |
| `GET` | `/tasks` | Retrieve all tasks | `200` | - |
| `GET` | `/tasks/{task_id}` | Retrieve a task by its ID | `200` | `404`, `422` |
| `POST` | `/tasks` | Create a new task | `201` | `400`, `422` |
| `PUT` | `/tasks/{task_id}` | Update an existing task by its ID | `200` | `400`, `404`, `422` |
| `DELETE` | `/tasks/{task_id}` | Delete a task by its ID | `204` | `404`, `422` |

## Example request

Create a task with `curl`:

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk","done":false}'
```

Example response:

```http
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

<img width="1415" height="877" alt="Screenshot (3226)" src="https://github.com/user-attachments/assets/9dd36388-ce45-4d2f-bb95-6d7a45cbed65" />

## Notable bugs found while building this

### Duplicate ID collision

Early on I computed new IDs as `len(tasks) + 1`. After a delete, this could
produce a duplicate ID. For example, deleting task 2 from a three-task list
and then creating a new task would assign it ID 3, colliding with the existing
task 3. Since my lookup returns the first match it finds, the second task with
that ID would become permanently unreachable: you could create it, but never
GET, PUT, or DELETE it by ID again.

This was fixed by computing the next ID as the current maximum ID in the list
plus 1, instead of relying on the list length.

### 422 vs. 400 on invalid input

The assignment specification says invalid input should return 400. My API does
this for a present-but-empty title (`{"title": ""}`) through its own
validation check. However, if `title` is missing from the request body
entirely (`{}`), Pydantic's built-in required-field validation rejects it
first, before my code runs, and returns 422 instead.

A client that only handles 400 based on the specification would miss this case.
The request is still correctly rejected and no task is created, but the failure
comes back in a shape the specification does not mention. I left this as a
known deviation rather than forcing both cases to return 400.

### Undocumented Swagger response shape

Swagger's auto-generated docs show a generic `"string"` as the example response
for `GET /tasks/{task_id}` instead of the real task shape, and do not list 404
as a possible response. This happens because I never declared a `response_model`
or return type.

The API's actual behavior and its documented contract diverge here. In a real
production API, this would be worth fixing with `response_model` declarations.

## AI vs me

### My prompt (Stage 7, written from memory)

```text
I want you to build a simple CRUD ToDo API using Python + FastAPI(uvicorn server). 
Start with three given tasks with keys: id: 1, title: (up to you), done: True/False.
The API Should consist of GET(All tasks), GET(Health status), GET(task_id),
POST, PUT, and DELETE with proper descriptions for each. These should handle different
error and invalid cases then return JSONResponse of specific status code such as 400, 404, 422
and others with the necessary message with it. You should also consider using pydantic class for validating task and task update variables.
```

### What did the AI do better?

* **OpenAPI Documentation Quality:** Added tags (`Tasks`, `System`), summaries, descriptions, and explicit `response_model` types for clean, complete Swagger UI docs instead of untyped `200` responses.
* **Separation of Concerns:** Split schemas into `TaskCreate`, `TaskUpdate`, and `TaskResponse` to prevent clients from attempting to inject IDs during creation.
* **Path Validation:** Used `Path(..., gt=0)` to catch invalid IDs (`<= 0`) at the framework layer before hitting business logic.
* **Avoided Naive List-Length ID Bugs:** Keyed `max(tasks_db.keys()) + 1` directly off dictionary keys rather than a naive collection length (`len()`), preventing the ID duplicate collisions that occur when middle items are deleted.

### What did the AI get wrong or quietly ignore?

* **`DELETE` Status Contract:** Returned `200 OK` with an acknowledgment JSON body instead of the standard REST convention of `204 No Content` with an empty body.

### What did my prompt forget to specify?

* **Root Endpoint (`GET /`):** Completely omitted the front-door metadata endpoint and its required JSON payload from the prompt's endpoint list.
* **Exact Error Schema:** Asked for error responses without specifying the required target key format (`{"error": "<msg>"}`), leading the AI to invent its own nested `{"status": "error", "message": "..."}` envelope.
* **`204` Deletion Semantics:** Failed to specify that a successful deletion must return `204 No Content` with an empty response body.
* **Status Code Boundaries (400 vs. 422):** Grouped status codes together ("400, 404, 422") without defining which scenario triggers which code; because empty strings were not explicitly designated for `400`, the AI made the defensible choice to enforce string constraints via Pydantic (`min_length=1`), routing empty strings to `422 Unprocessable Entity`.

---

### The Rematch: Prompt v2 (Written from the findings)

```text
Build a CRUD ToDo API using Python + FastAPI and Uvicorn with in-memory storage seeded with 3 example tasks (id, title, done).

Include these exact endpoints:
- GET /: returns {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}
- GET /health: returns {"status": "ok"}
- GET /tasks: returns the list of all tasks
- GET /tasks/{task_id}: returns the task by ID, or 404 with {"error": "Task {id} not found"}
- POST /tasks: accepts {"title": "..."}; returns 201 with the new task; if title is missing or empty string "", return 400 with {"error": "Title cannot be empty"}
- PUT /tasks/{task_id}: updates title and/or done; returns the updated task; return 404 if missing, or 400 with {"error": "..."} if empty body or invalid title
- DELETE /tasks/{task_id}: removes task and returns status 204 with an empty body; return 404 with {"error": "Task {id} not found"} if missing

Ensure all error responses strictly follow the flat JSON shape {"error": "<message>"}. Use Pydantic for validation, and include clean endpoint descriptions and tags for Swagger UI.
```

**What changed:** Prompt v2 eliminated specification gaps by explicitly defining the root metadata endpoint, binding each HTTP status code directly to its trigger condition, enforcing a flat `{"error": "..."}` schema, and mandating `204 No Content` with an empty body for deletions.
