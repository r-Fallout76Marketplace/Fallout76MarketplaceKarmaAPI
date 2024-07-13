from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, cast

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from db_operations import UserProfile, add_user_profile, find_profile, get_karma_db, get_mongo_collection, update_user_profile

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with get_karma_db() as karma_db:
        app.state.karma_db = karma_db
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse("/docs")


async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return cast(AsyncIOMotorDatabase, request.app.state.karma_db)


class Message(BaseModel):
    message: str


@app.get(
    path="/users/{reddit_username}",
    response_model=UserProfile,
    summary="Get KarmaProfile by Reddit username.",
    responses={404: {"model": Message}},
)
async def get_user(reddit_username: str, karma_db: AsyncIOMotorDatabase = Depends(get_db)) -> UserProfile | JSONResponse:
    user_karma_collection = await get_mongo_collection("user_karma", karma_db)
    user_profile = await find_profile(reddit_username, user_karma_collection)
    if user_profile is None:
        return JSONResponse(status_code=404, content={"message": f"Reddit username '{reddit_username}' not found"})
    return user_profile


@app.put(
    path="/users/profile",
    summary="Update existing KarmaProfile for Reddit username.",
    responses={
        200: {"model": Message},
        404: {"model": Message},
    },
)
async def update_gamertag(user_profile: UserProfile, karma_db: AsyncIOMotorDatabase = Depends(get_db)) -> JSONResponse:
    user_karma_collection = await get_mongo_collection("user_karma", karma_db)
    status = await update_user_profile(user_profile=user_profile, users_collection=user_karma_collection)
    if status:
        return JSONResponse(status_code=200, content={"message": f"Karma Profile updated successfully for Reddit username: {user_profile.reddit_username}."})
    else:
        return JSONResponse(status_code=404, content={"message": f"Reddit username '{user_profile.reddit_username}' not found."})


@app.post(
    path="/users/profile",
    summary="Add new KarmaProfile for Reddit username.",
    responses={
        200: {"model": Message},
        400: {"model": Message},
    },
)
async def add_profile(user_profile: UserProfile, karma_db: AsyncIOMotorDatabase = Depends(get_db)) -> JSONResponse:
    user_karma_collection = await get_mongo_collection("user_karma", karma_db)
    status = await add_user_profile(user_profile=user_profile, users_collection=user_karma_collection)
    if status:
        return JSONResponse(status_code=200, content={"message": f"Karma Profile added successfully for Reddit username: {user_profile.reddit_username}."})
    else:
        return JSONResponse(status_code=400, content={"message": "Profile already exists or invalid fields in user profile."})
