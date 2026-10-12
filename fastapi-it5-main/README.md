# Beginner FastAPI + SQLite

This repository is a starter project for students who want to build their own backend API and database app in Python. It shows the basic pattern for:

- creating Python classes for request and response data
- writing SQL queries against SQLite
- creating REST API endpoints in FastAPI

Use it as a template for your own project. Replace the student example with your own data model, table name, and endpoints.

## Run it on Windows

From this folder, create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Then open <http://127.0.0.1:8000/docs> in your browser. The API docs page will let you try the project without writing a separate client.

## Project structure

- `main.py` creates the FastAPI app and defines the routes.
- `app/database.py` opens SQLite connections and creates tables.
- `app/models.py` defines the Pydantic data classes.
- `students.db` is the SQLite database file created the first time the app runs.

## How to make your own classes

The project already uses a simple pattern: a Pydantic model describes the data, and the route functions call helper methods on that model.

Example from `app/models.py`:

```python
from pydantic import BaseModel, Field


class StudentInput(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0)


class Student(StudentInput):
    id: int
```

To make your own class for a different project, follow the same pattern:

```python
from pydantic import BaseModel, Field


class CourseInput(BaseModel):
    title: str = Field(min_length=1)
    credits: int = Field(ge=0)


class Course(CourseInput):
    id: int
```

A model class is useful because FastAPI can validate incoming JSON automatically and return the data in a consistent format.

## How to make your own SQL queries

The database connection is managed in `app/database.py`:

```python
@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
```

Use it like this when you write your own queries:

```python
with database_connection() as connection:
    rows = connection.execute(
        "SELECT id, title, credits FROM courses WHERE id = ?",
        (course_id,),
    ).fetchall()
```

Important ideas:

- `CREATE TABLE` defines a new table.
- `INSERT` adds rows.
- `SELECT` reads data.
- `UPDATE` changes data.
- `DELETE` removes data.
- Use `?` placeholders instead of string concatenation to keep SQL safe.

Example table setup:

```python
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        credits INTEGER NOT NULL CHECK (credits >= 0)
    )
    """
)
```

## How to make your own endpoints

FastAPI routes live in `main.py`. Each function is connected to an HTTP method and path using decorators like `@app.get`, `@app.post`, `@app.put`, and `@app.delete`.

Example:

```python
@app.get("/courses")
def get_courses():
    result = Course.list_courses(database_connection=database_connection)
    return {"courses": result}


@app.post("/course")
def create_course(course: CourseInput):
    result = Course.create_course(
        course_input=course,
        database_connection=database_connection,
    )
    return {"course": result}
```

The route function usually does three things:

1. accept a request body or URL parameter
2. call a SQL query through a model helper
3. return JSON for the client

## Reuse this pattern for your own project

A good project workflow is:

1. Create a new model class in `app/models.py`.
2. Add a table in `app/database.py` with `CREATE TABLE IF NOT EXISTS`.
3. Add SQL helper methods to your model class.
4. Add a route in `main.py` that calls those helper methods.
5. Test the endpoint in the Swagger UI at `/docs`.

For example, if your project is about books, students, courses, or games, you can copy this structure and replace `Student` with your own concept. The pattern stays the same even when the data changes.

## Current example endpoints

This starter project already includes these routes:

- `GET /` returns a welcome message
- `GET /students` lists students
- `GET /students/{student_id}` gets one student
- `POST /student` creates a student
- `PUT /student/{student_id}` updates a student
- `DELETE /student/{student_id}` deletes a student

Use these as examples when building your own API routes.


