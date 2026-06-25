from datetime import datetime
from random import randint
from typing import Any
from fastapi import FastAPI, HTTPException, Response
from sqlmodel import Field, Session, SQLModel, create_engine, select

import os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None 
    created_at: datetime


PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PH_HOST = os.getenv("PH_HOST")
PG_DB = os.getenv("PG_DB")

postgres_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PH_HOST}:5432/{PG_DB}"

connect_args = {"check_same_thread": False}
engine = create_engine(postgres_url,connect_args=connect_args) # Used to interact with the postgres DB


campaigns: Any = [
    {
        "campaign_id": 1,
        "name": "Youth Day Special",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 2,
        "name": "Black Friday Bonanza",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 3,
        "name": "Xmas",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    }
]

# GET endpoint for the homepage
@app.get("/")
async def get_campaigns():
    return {"Message": "Hellow World"}

@app.get("/campaigns")
async def read_campaigns():
    return {"Campaigns": campaigns }


@app.get("/campaigns/{id}")
async def read_campaign(id: int):
    if id > (len(campaigns)):
        raise HTTPException(status_code=404)
    else:
        return campaigns[id-1]
        
@app.post("/campaigns")
async def create_campaign(campaign: dict[str, Any]):

    new_campaign: dict[str, Any] = {
        "campaign_id": randint(100, 200),
        "name": campaign.get('name'),
        "due_date": campaign.get('due_date'),
        "created_at": datetime.now()
    }

    campaigns.append(new_campaign)
    return {"New campaign": new_campaign}


@app.put("/campaigns/{id}", status_code=201)
async def update_campaign(id: int, body: dict[str, Any]):

    for index, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == id:
            update: dict[str, Any] = {
                "campaign_id": id,
                "name": body.get('name'),
                "due_date": body.get('due_date'),
                "created_at": campaign.get("created_at")
            }

            campaigns[index] = update
            return {"update": update}
    raise HTTPException(status_code=404)

@app.delete("/campaigns/{id}")
async def delete_campaign(id: int):

    for index, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == id:
            campaigns.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404)

