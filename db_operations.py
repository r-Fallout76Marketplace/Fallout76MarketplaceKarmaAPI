from __future__ import annotations

from contextlib import asynccontextmanager
from os import getenv
from typing import AsyncGenerator, Literal, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pydantic import BaseModel, Field


@asynccontextmanager
async def get_karma_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Returns the MongoDB AsyncIOMotorClient

    :returns: AsyncIOMotorClient object
    :rtype: AsyncIOMotorClient

    """
    cluster = AsyncIOMotorClient(getenv("MONGO_PASS", "MONGO_PASS"))
    try:
        yield cluster["fallout76marketplace_karma_db"]
    finally:
        cluster.close()


async def get_mongo_collection(collection_name: str, fallout76marketplace_karma_db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    """Returns the user databased from dataBased Cluster from MongoDB

    :returns: Returns a Collection from Mongo DB

    """
    return fallout76marketplace_karma_db[collection_name]


class Gamertag(BaseModel):
    gamertag: str = Field(..., min_length=1)
    gamertag_id: str = Field(..., min_length=1, pattern=r"^\d+$")
    platform: Literal["XBOX", "PlayStation", "PC"]


class UserProfile(BaseModel):
    reddit_username: str
    karma: int
    gamertags: list[Gamertag]
    m76_karma: int


async def find_profile(reddit_username: str, users_collection: AsyncIOMotorCollection) -> Optional[UserProfile]:
    """Finds the user in the users_collection, or creates one if it doesn't exist using default values.

    :param reddit_username: The user whose profile to find or create
    :param users_collection: The collection in which the profile will be searched or inserted

    :returns: Dict object with user profile info

    """
    profile = await users_collection.find_one({"reddit_username": reddit_username})
    if profile is None:
        return None

    return UserProfile(**profile)


async def update_user_profile(user_profile: UserProfile, users_collection: AsyncIOMotorCollection) -> bool:
    profile = await users_collection.find_one({"reddit_username": user_profile.reddit_username})
    if profile is not None:
        await users_collection.replace_one({"reddit_username": user_profile.reddit_username}, user_profile.model_dump())
        return True
    return False
