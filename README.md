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
