from dataclasses import asdict
from datetime import datetime
import os
import asyncio
from unittest import result
from quart import Quart
from databases import Database
from datetime import datetime
from typing import Optional
from time import sleep
from pydantic.dataclasses import dataclass
from quart_schema import QuartSchema, validate_request, validate_response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Quart(__name__)
QuartSchema(app)
app.config.update({
    "DATABASE_URL": "sqlite+aiosqlite:///todo.db",
})


@app.route("/")
async def index() -> str:
    count_todos = await app.db.fetch_val("Select count(*) from todos")
    return f"There are {count_todos} todos"


@dataclass
class TodoData:
    complate: bool
    due: Optional[datetime]
    task: str


@dataclass
class Todo(TodoData):
    id: int | None


@app.route("/todos/", methods=["POST"])
@validate_request(TodoData)
@validate_response(Todo, 201)
async def create_todo(data: TodoData) -> Todo:
    """" Create a new todo.
        -> Request: 
            - complate: bool
            - due: datetime
            - task: str
        -> Response: 
            - id: int
            - complate: bool
            - due: datetime
            - task: str
    """
    id_ = await app.db.fetch_val(
        """INSERT INTO todos(complate, due, task) 
                VALUES(:complate, :due, :task)
            RETURNING id""",
        values=asdict(data),

    )
    return Todo(id=id_, **asdict(data))


@dataclass
class Todos:
    todos: list[Todo]


@app.route("/todos/", methods=["GET"])
@validate_response(Todos)
async def get_todos() -> Todos:
    """" Gel all todos
        -> Response: [
            {
                id: int
                complate: bool
                due: datetime
                task: str
            }
        ] 
    """
    result = await app.db.fetch_all(
        """Select * from todos;"""
    )
    todos_ = [Todo(**row) for row in result]
    return Todos(todos=todos_)


async def _create_db_connection() -> Database:
    db = Database(app.config["DATABASE_URL"])
    await db.connect()
    return db


@app.cli.command("init_db")
def init_db() -> None:
    async def _inner() -> None:
        db = await _create_db_connection()
        with open(os.path.join(BASE_DIR, "schema.sql"), "r") as file_:
            for command in file_.read().split(";"):
                await db.execute(command)
    asyncio.run(_inner())


@app.before_serving
async def startup() -> None:
    app.db = await _create_db_connection()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5000')
