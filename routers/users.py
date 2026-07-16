from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import ResponseUser, UpdateUser, CreateUser, ResponseCampaign

router = APIRouter()


# [API] Fecth all users - Only API, why would users get access to view site users?
@router.get(path="", response_model=list[ResponseUser])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Users))
    users = result.scalars()

    if users:
        return users
    return "No users found"


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
    )
    campaigns = result.scalars().all()

    if campaigns:
        return campaigns
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found"
    )


# [API] Create user
@router.post(path="", response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Users.user_id).where(models.Users.email == user.email)
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    new_user = models.Users(username=user.username, email=user.email)

    db.add(new_user)  # stages the new user
    await db.commit()  # commits the change (IT DOES COMETHING)
    await db.refresh(new_user)
    return new_user


# [API] PATCH ENDPOINT TO UPDATE A USER BY THEIR USER_ ID
@router.patch(path="/{user_id}", response_model=ResponseUser)
async def update_user_partial(
    user_id: int, user_data: UpdateUser, db: Annotated[AsyncSession, Depends(get_db)]
):

    # Check user exists
    result = await db.execute(
        select(models.Users).where(models.Users.user_id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    if (
        user_data.username != None and user_data.username != user.username
    ):  # Check if new username doesn't match old username
        user_result = await db.execute(
            select(models.Users).where(models.Users.username == user_data.username)
        )  # Check if new username doesn't match username in DB
        existing_user = user_result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_data.email != None and user_data.email != user.email:
        email_result = await db.execute(
            select(models.Users).where(models.Users.email == user_data.email)
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
@router.delete(path="/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    results = await db.execute(
        select(models.Users).where(models.Users.user_id == user_id)
    )
    user = results.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    await db.delete(user)
    await db.commit()
