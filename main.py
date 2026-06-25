from datetime import datetime
from random import randint
from typing import Any
from fastapi import FastAPI, HTTPException, Response

app = FastAPI()


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

