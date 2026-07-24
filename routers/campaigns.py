from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import UpdateCampaign, CreateCampaign, ResponseCampaign
from auth import CurrentUser

router = APIRouter()


# [API] CAMPAIGNS HOMEPAGE ENDPOINT
@router.get(path="", response_model=list[ResponseCampaign])
async def get_campaigns(db: Annotated[AsyncSession, Depends(get_db)]):
    query = await db.execute(
        select(models.Campaigns)
        .options(
            selectinload(
                models.Campaigns.author
            )  # selectinload tells the fucntion to also load relationship when it loads up the model
        )
        .order_by(models.Campaigns.created_at.desc())
    )
    campaigns = query.scalars().all()

    return campaigns


# [API] FETCH CAMPAIGN BY ID
@router.get(path="/{campaign_id}", response_model=ResponseCampaign)
async def get_campaign(campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Campaigns)
        .options(selectinload(models.Campaigns.author))
        .where(models.Campaigns.campaign_id == campaign_id)
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
    campaign: CreateCampaign, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
): # Since CurrentUser checks of the user exists, we no longer need the user check in the endpoint
 
    new_campaign = models.Campaigns(
        campaign_name=campaign.campaign_name,
        user_id=current_user.user_id,
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
    current_user: CurrentUser,
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
    if campaign.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )

    campaign.campaign_name = campaign_data.campaign_name
    campaign.campaign_details = campaign_data.campaign_details

    await db.commit()
    await db.refresh(campaign, attribute_names=["author"])
    return campaign


# [API] PATCH ENDPOINT TO UPDATE A CAMPAIGN BY ID
@router.patch(path="/{campaign_id}", response_model=ResponseCampaign)
async def update_campaign_partial(
    campaign_id: int,
    campaign_data: UpdateCampaign,
    current_user: CurrentUser,
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
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No campaigns found"
        )
    
    if campaign.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
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
    campaign_id: int,
    current_user: CurrentUser, 
    db: Annotated[AsyncSession, Depends(get_db)]
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

    if campaign.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )
    
    await db.delete(campaign)
    await db.commit()
