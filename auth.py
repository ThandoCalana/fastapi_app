# Authentication utilities

import jwt
from datetime import UTC, timedelta, datetime
from pwdlib import PasswordHash
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer  # Handles token-based authentication
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models
from database import get_db

from config import settings

password_hasher = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/users/token"  # Indicates where to send username and password to fetch access token
)


def hash_password(password: str) -> str:  # creates the hashed password
    return password_hasher.hash(password)


def verify_password(
    plain_password: str, hashed_password: str
) -> (
    bool
):  # Verifies what we just received against what we have (usually user input vs. password hash in or db)
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict, expire_time: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expire_time:
        expire = datetime.now(UTC) + expire_time
    else:
        expire = datetime.now(UTC) + timedelta(settings.access_token_expire_minutes)

    to_encode["exp"] = expire
    jwt_token = jwt.encode(
        payload=to_encode,
        key=settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return jwt_token


def verify_access_token(token: str) -> str | None:
    """Verify a JWT Token and return the subject (user ID) if the token is valid"""
    try:
        decoded_token = jwt.decode(
            jwt=token,
            key=settings.secret_key.get_secret_value(),
            algorithms=settings.algorithm,
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:

        return decoded_token.get("sub")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.Users:
    """This function serves as endpoint 'protection' and creates an authorization dependency on all routes it is used in.
    The function's aim is to:
           - verify the user by taking in its token
           - type casts their user_id to ensure it's a valid token
           - check against the DB to ensure that there is a user associated with the given user_id (extracted form token)
           - return the user
           - ensure that they are authorized (allowed to access the resource)"""

    # Verify user_id
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # type cast to int
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = db.execute(select(models.Users).where(models.Users.user_id == user_id_int))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# This variable creates an instance of the user with the dependency => return user once if authorized and authenticated
CurrentUser = Annotated[models.Users, Depends(get_current_user)]
