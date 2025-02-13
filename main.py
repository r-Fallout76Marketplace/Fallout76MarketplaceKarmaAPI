from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
)
from fastapi.responses import RedirectResponse

from db_operations import (
    get_karma_db,
)
from db_routes import protected_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage the application's lifespan by setting up and tearing down the karma database connection.

    This context manager is responsible for:

    - Initializing a database connection (via `get_karma_db()`) when the application starts.
    - Storing that connection in `app.state.karma_db`.
    - Properly closing or cleaning up the database connection after the application shuts down.

    :param app: The FastAPI application instance to which the database connection is attached.
    :yields: Nothing is explicitly yielded (returns None), but the context remains active during the application's lifetime.
    """
    async with get_karma_db() as karma_db:
        app.state.karma_db = karma_db
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(protected_router)


@app.get("/")
async def redirect_to_docs() -> RedirectResponse:
    """
    Redirect the root path ("/") to the API docs ("/docs").

    :return: A redirect response object that sends the user to "/docs".
    """
    return RedirectResponse("/docs")
