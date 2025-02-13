from __future__ import annotations

from contextlib import asynccontextmanager
from os import getenv
from typing import TYPE_CHECKING, Literal

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def get_karma_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Returns the MongoDB AsyncIOMotorClient.

    :returns: AsyncIOMotorClient object
    :rtype: AsyncIOMotorClient

    """
    cluster = AsyncIOMotorClient(getenv("MONGO_PASS", "MONGO_PASS"))
    try:
        yield cluster["fallout76marketplace_karma_db"]
    finally:
        cluster.close()


async def get_mongo_collection(collection_name: str, fallout76marketplace_karma_db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    """
    Returns the user databased from dataBased Cluster from MongoDB.

    :returns: Returns a Collection from Mongo DB

    """
    return fallout76marketplace_karma_db[collection_name]


class Gamertag(BaseModel):
    """
    Represents a gaming account identifier.

    :param gamertag: The user's handle on the gaming platform.
    :type gamertag: str
    :param gamertag_id: A numeric identifier for the gamertag.
    :type gamertag_id: str
    :param platform: The gaming platform (XBOX, PlayStation, or PC).
    :type platform: Literal["XBOX", "PlayStation", "PC"]
    """

    gamertag: str = Field(..., min_length=1)
    gamertag_id: str = Field(..., min_length=1, pattern=r"^\d+$")
    platform: Literal["XBOX", "PlayStation", "PC"]


class UserProfile(BaseModel):
    """
    A user's trading profile for Fallout 76 subreddits.

    :param reddit_username: The user's Reddit handle.
    :type reddit_username: str
    :param karma: Trading karma for r/Fallout76Marketplace.
    :type karma: int
    :param gamertags: A list of gaming account identifiers.
    :type gamertags: list[Gamertag]
    :param m76_karma: Trading karma for r/Market76.
    :type m76_karma: int
    """

    reddit_username: str
    karma: int
    gamertags: list[Gamertag]
    m76_karma: int


async def find_profile(reddit_username: str, users_collection: AsyncIOMotorCollection) -> UserProfile | None:
    """
    Finds the user in the users_collection, or creates one if it doesn't exist using default values.

    :param reddit_username: The user whose profile to find or create
    :param users_collection: The collection in which the profile will be searched or inserted

    :returns: Dict object with user profile info

    """
    profile = await users_collection.find_one({"reddit_username": reddit_username})
    if profile is None:
        return None

    return UserProfile(**profile)


async def update_user_profile(user_profile: UserProfile, users_collection: AsyncIOMotorCollection) -> bool:
    """
    Update an existing user profile in the database.

    This function checks if a profile with the given Reddit username exists. If it does,
    it replaces the existing document with the new data from the provided `user_profile`.
    Returns True if the profile was successfully updated, otherwise False.

    :param user_profile: The user profile data to be updated.
    :param users_collection: The MongoDB collection where user profiles are stored.
    :return: True if the profile was found and updated, otherwise False.
    """
    profile = await users_collection.find_one({"reddit_username": user_profile.reddit_username})
    if profile is not None:
        await users_collection.replace_one({"reddit_username": user_profile.reddit_username}, user_profile.model_dump())
        return True
    return False


async def add_user_profile(user_profile: UserProfile, users_collection: AsyncIOMotorCollection) -> bool:
    """
    Insert a new user profile into the database.

    This function checks if a profile with the given Reddit username already exists.
    If it does not, it inserts a new document with the provided user profile data.
    Returns True if the insert was acknowledged, otherwise False.

    :param user_profile: The user profile data to be inserted.
    :param users_collection: The MongoDB collection where user profiles are stored.
    :return: True if the profile was inserted successfully (acknowledged), otherwise False.
    """
    profile = await users_collection.find_one({"reddit_username": user_profile.reddit_username})

    if profile is not None:
        return False

    insert_result = await users_collection.insert_one(
        {
            "reddit_username": user_profile.reddit_username,
            "karma": user_profile.karma,
            "m76_karma": user_profile.m76_karma,
            "gamertags": user_profile.gamertags,
        },
    )

    return insert_result.acknowledged
