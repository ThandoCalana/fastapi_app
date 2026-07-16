from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import UpdateCampaign, CreateCampaign, ResponseCampaign

router = APIRouter()


# [API] CAMPAIGNS HOMEPAGE ENDPOINT
@router.get(path="", response_model=list[ResponseCampaign])
async def get_campaigns(db: Annotated[AsyncSession, Depends(get_db)]):
    query = await db.execute(
        select(models.Campaigns).options(
            selectinload(
                models.Campaigns.author
            )  # selectinload tells the fucntion to also load relationship when it loads up the model
        )
    )
    campaigns = query.scalars().all()

    return campaigns


# [API] FETCH CAMPAIGN BY ID
@router.get(
    path="/{campaign_id}", response_model=ResponseCampaign
)
async def get_campaign(campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Campaigns).options(
            selectinload(
                models.Campaigns.author
            )
        ).where(models.Campaigns.campaign_id == campaign_id)
    )
    campaign = result.scalars().first()  # selects one or none, Returns None
    # users = query.scalar_one() raises an error if nothing is found

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found"
        )

    return campaign


# [API] Create new campaign
@router.post(
    path="",
    response_model=ResponseCampaign,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    campaign: CreateCampaign, db: Annotated[AsyncSession, Depends(get_db)]
):

    new_campaign = models.Campaigns(
        campaign_name=campaign.campaign_name,
        user_id=campaign.user_id,
        campaign_details=campaign.campaign_details,
        created_at=datetime.now(),
    )

    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign, attribute_names=["author"])

    return new_campaign


# [API] PUT ENDPOINT TO UPDATE A CAMPAIGN BY ID
@router.put(path="/{campaign_id}", response_model=ResponseCampaign)
async def update_campaign_full(
    campaign_id: int,
    campaign_data: CreateCampaign,
    db: Annotated[AsyncSession, Depends(get_db)],
):

    result = await db.execute(
        select(models.Campaigns)
        .options(selectinload(models.Campaigns.author))
        .where(models.Campaigns.campaign_id == campaign_id)
    )
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    if campaign_data.user_id != campaign.user_id:
        user_check = await db.execute(
            select(models.Users).where(models.Users.user_id == campaign_data.user_id)
        )
        user = user_check.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    campaign.campaign_name = campaign_data.campaign_name
    campaign.campaign_details = campaign_data.campaign_details
    campaign.user_id = campaign_data.user_id

    await db.commit()
    await db.refresh(campaign, attribute_names=["author"])
    return campaign


# [API] PATCH ENDPOINT TO UPDATE A CAMPAIGN BY ID
@router.patch(path="/{campaign_id}", response_model=ResponseCampaign)
async def update_campaign_partial(
    campaign_id: int,
    campaign_data: UpdateCampaign,
    db: Annotated[AsyncSession, Depends(get_db)],
):

    # Check campaign exists
    result = await db.execute(
        select(models.Campaigns)
        .options(selectinload(models.Campaigns.author))
        .where(models.Campaigns.campaign_id == campaign_id)
    )
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found"
        )

    update_data = campaign_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    await db.commit()
    await db.refresh(
        campaign, attribute_names=["author"]
    )  # Load specific relationships using the attriute name
    return campaign


# [API] DELETE CAMPAIGNS BY ID
@router.delete(path="/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):

    results = await db.execute(
        select(models.Campaigns)
        .options(selectinload(models.Campaigns.author))
        .where(models.Campaigns.campaign_id == campaign_id)
    )
    campaign = results.scalars().first()

    # Need to add checks to make sure the user making the delete is the author of the campaign

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No campaign found"
        )

    await db.delete(campaign)
    await db.commit()
