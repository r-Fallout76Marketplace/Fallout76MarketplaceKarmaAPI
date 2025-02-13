from __future__ import annotations

import secrets
from os import getenv
from typing import Annotated, Literal, cast

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Security,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from db_operations import (
    UserProfile,
    add_user_profile,
    find_profile,
    get_mongo_collection,
    update_user_profile,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> Literal[True]:
    """
    Validate an incoming API key against an environment variable.

    The function checks for an API key in the request via the `api_key_header`
    security scheme. If the key is missing or does not match the value of the
    `API_KEY` environment variable, it raises a 403 `HTTPException`. If the
    environment variable is not set, a random key is generated (using
    `secrets.token_hex(32)`) for comparison, resulting in an automatic
    mismatch unless the same generated key is used consistently.

    :param api_key: The API key provided in the request header.
    :return: True if the provided API key is valid, otherwise raises an exception.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API Key",
        )
    if not secrets.compare_digest(api_key, getenv("API_KEY", secrets.token_hex(32))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return True


protected_router = APIRouter(
    prefix="/api",
    dependencies=[Depends(verify_api_key)],
)


async def get_db(request: Request) -> AsyncIOMotorDatabase:
    """
    Retrieve the MongoDB database connection from the FastAPI application state.

    :param request: The current request, which contains the FastAPI app with attached state.
    :return: An asynchronous Motor database instance for performing queries.
    """
    return cast(AsyncIOMotorDatabase, request.app.state.karma_db)


class Message(BaseModel):
    """
    A simple message model used for API responses.

    This model encapsulates a single string field named "message",
    which is commonly used to provide a status or error description
    in the API responses.

    :param message: A textual message describing the status, error, or feedback to the client.
    :type message: str
    """

    message: str


@protected_router.get(
    path="/users/{reddit_username}",
    response_model=UserProfile,
    summary="Get KarmaProfile by Reddit username.",
    responses={404: {"model": Message}},
)
async def get_user(reddit_username: str, karma_db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]) -> UserProfile | JSONResponse:
    """
    Retrieve a user's trading profile based on their Reddit username.

    This endpoint checks the "user_karma" collection for a document matching
    the specified username. If found, it returns a ``UserProfile`` model.
    Otherwise, it returns a 404 JSON response with an error message.

    :param reddit_username: The Reddit username to look up.
    :param karma_db: The async database instance used to query user data.
    :return: A ``UserProfile`` if the user is found, or a 404 JSON response.
    """
    user_karma_collection = await get_mongo_collection("user_karma", karma_db)
    user_profile = await find_profile(reddit_username, user_karma_collection)
    if user_profile is None:
        return JSONResponse(status_code=404, content={"message": f"Reddit username '{reddit_username}' not found"})
    return user_profile


@protected_router.put(
    path="/users/profile",
    summary="Update existing KarmaProfile for Reddit username.",
    responses={
        200: {"model": Message},
        404: {"model": Message},
    },
)
async def update_gamertag(user_profile: UserProfile, karma_db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]) -> JSONResponse:
    """
    Update an existing KarmaProfile in the database for the specified Reddit username.

    This endpoint updates a user profile document in the "user_karma" collection
    with the data provided in ``user_profile``. If the profile is found and updated
    successfully, a JSON response with a 200 status code is returned. If no profile
    with the given username exists, a 404 JSON response is returned.

    :param user_profile: The updated user profile data.
    :param karma_db: An asynchronous database connection used to update the user profile.
    :return: A JSON response indicating a successful update (200) or a not-found error (404).
    """
    user_karma_collection = await get_mongo_collection("user_karma", karma_db)
    status = await update_user_profile(user_profile=user_profile, users_collection=user_karma_collection)
    if status:
        return JSONResponse(status_code=200, content={"message": f"Karma Profile updated successfully for Reddit username: {user_profile.reddit_username}."})
    return JSONResponse(status_code=404, content={"message": f"Reddit username '{user_profile.reddit_username}' not found."})


@protected_router.post(
    path="/users/profile",
    summary="Add new KarmaProfile for Reddit username.",
    responses={
        200: {"model": Message},
        400: {"model": Message},
    },
)
async def add_profile(user_profile: UserProfile, karma_db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]) -> JSONResponse:
    """
    Create a new KarmaProfile in the database for the specified Reddit username.

    This endpoint inserts a new user profile document into the "user_karma" collection.
    If the profile is successfully added, it returns a JSON response with a 200 status code.
    If a profile with the same username already exists or the provided data is invalid,
    it returns a JSON response with a 400 status code and an error message.

    :param user_profile: The user profile data to be added.
    :param karma_db: An asynchronous database connection for inserting the user profile.
    :return: A JSON response indicating success (200) or an error (400).
    """
    user_karma_collection = await get_mongo_collection("user_karma", karma_db)
    status = await add_user_profile(user_profile=user_profile, users_collection=user_karma_collection)
    if status:
        return JSONResponse(status_code=200, content={"message": f"Karma Profile added successfully for Reddit username: {user_profile.reddit_username}."})
    return JSONResponse(status_code=400, content={"message": "Profile already exists or invalid fields in user profile."})
