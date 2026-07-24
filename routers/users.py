from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

import models
from config import settings
from database import get_db
from schemas import (
    PrivateUser,
    PublicUser,
    UpdateUser,
    CreateUser,
    ResponseCampaign,
    Token,
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    CurrentUser
)

router = APIRouter()


# [API] Fecth all users - Only API, why would users get access to view site users?
@router.get(path="", response_model=list[PublicUser])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Users))
    users = result.scalars()

    if users:
        return users
    return "No users found"


# The following endpoint is important as it validates the user's token is still good AND provides the user's full details
@router.get(path="/me", response_model=PrivateUser)
async def get_current_user(current_user: CurrentUser):
    return current_user


# [API] Fecth user by USER ID
@router.get(path="/{user_id}", response_model=PublicUser)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user_check = await db.execute(
        select(models.Users).where(models.Users.user_id == user_id)
    )
    user = user_check.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


# [API] Fecth current user's campaigns
@router.get(path="/{user_id}/campaigns", response_model=list[ResponseCampaign])
async def user_campaigns(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user_check = await db.execute(
        select(models.Users).where(models.Users.user_id == user_id)
    )
    user_check_result = user_check.scalars().first()

    if not user_check_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    result = await db.execute(
        select(models.Campaigns)
        .options(selectinload(models.Campaigns.author))
        .where(models.Campaigns.user_id == user_id)
        .order_by(models.Campaigns.created_at.desc)
    )
    campaigns = result.scalars().all()

    if campaigns:
        return campaigns
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found"
    )


# [API] Create user
@router.post(path="", response_model=PrivateUser, status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Users.user_id).where(
            func.lower(models.Users.username) == user.username.lower()
        )  # func.lower => case insensitivity
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    email_result = await db.execute(
        select(models.Users.user_id).where(
            func.lower(models.Users.email) == user.email.lower()
        )
    )
    existing_email = email_result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user = models.Users(
        username=user.username,  # keeping the case for display, but still lowercase in validation
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )

    db.add(new_user)  # stages the new user
    await db.commit()  # commits the change (IT DOES COMETHING)
    await db.refresh(new_user)
    return new_user


# [API] Sends login info, then FETCHES user's token
@router.post(path="/token", response_model=Token, name="Login for User Token")
async def get_user_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Users).where(
            func.lower(models.Users.email) == form_data.username.lower()
        )
    )  # Request form uses email as their username

    user = result.scalars().first()

    if not user or verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_epxires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expire_time=access_token_epxires
    )

    return Token(access_token=access_token, token_type="Bearer")


# [API] PATCH ENDPOINT TO UPDATE A USER BY THEIR USER_ ID
@router.patch(path="/{user_id}", response_model=PrivateUser)
async def update_user_partial(
    user_data: UpdateUser, 
    user_id: int,
    current_user: CurrentUser, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    # Check user exists
    result = await db.execute(
        select(models.Users).where(models.Users.user_id == current_user.user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    if (
        user_data.username != None
        and user_data.username.lower() != user.username.lower()
    ):  # Check if new username doesn't match old username
        user_result = await db.execute(
            select(models.Users).where(
                func.lower(models.Users.username) == user_data.username.lower()
            )
        )  # Check if new username doesn't match username in DB
        existing_user = user_result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_data.email != None and user_data.email.lower() != user.email.lower():
        email_result = await db.execute(
            select(models.Users).where(
                func.lower(models.Users.email) == user_data.email.lower()
            )
        )
        existing_email = email_result.scalars().first()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    # OORR
    # if update_data.username is not None:
    #    user.username = update_data.username

    await db.commit()
    await db.refresh(user)
    return user


# [API] DELETE USER BY ID
@router.delete(path="/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    results = await db.execute(
        select(models.Users).where(models.Users.user_id == current_user.user_id)
    )
    user = results.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    await db.delete(user)
    await db.commit()
